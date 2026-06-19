"""Signup profile trigger and agent log realtime.

Revision ID: 0002_signup_realtime
Revises: 0001_profiles_jobs_actions
Create Date: 2026-06-19
"""

from alembic import op


revision = "0002_signup_realtime"
down_revision = "0001_profiles_jobs_actions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION public.normalize_profile_role(_role TEXT)
        RETURNS TEXT
        LANGUAGE sql
        IMMUTABLE
        AS $$
            SELECT CASE lower(replace(coalesce(_role, 'viewer'), '-', ' '))
                WHEN 'admin' THEN 'admin'
                WHEN 'farmer' THEN 'farmer'
                WHEN 'driver' THEN 'driver'
                WHEN 'store owner' THEN 'store_owner'
                WHEN 'store_owner' THEN 'store_owner'
                WHEN 'store manager' THEN 'store_owner'
                WHEN 'store_manager' THEN 'store_owner'
                WHEN 'pantry manager' THEN 'pantry_manager'
                WHEN 'pantry_manager' THEN 'pantry_manager'
                ELSE 'viewer'
            END
        $$;

        CREATE OR REPLACE FUNCTION public.handle_new_auth_user_profile()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = public
        AS $$
        DECLARE
            metadata JSONB;
            resolved_name TEXT;
            resolved_role TEXT;
        BEGIN
            metadata := COALESCE(NEW.raw_user_meta_data, '{}'::jsonb);
            resolved_name := COALESCE(NULLIF(metadata->>'full_name', ''), split_part(NEW.email, '@', 1), 'New User');
            resolved_role := public.normalize_profile_role(metadata->>'role');

            INSERT INTO public.user_profiles (auth_id, email, full_name, role)
            VALUES (NEW.id, NEW.email, resolved_name, resolved_role)
            ON CONFLICT (auth_id) DO UPDATE
            SET email = EXCLUDED.email,
                full_name = COALESCE(public.user_profiles.full_name, EXCLUDED.full_name),
                role = COALESCE(public.user_profiles.role, EXCLUDED.role),
                updated_at = NOW();

            RETURN NEW;
        END;
        $$;

        CREATE OR REPLACE FUNCTION public.register_user_profile(
            _auth_id UUID,
            _email TEXT,
            _full_name TEXT,
            _role TEXT
        )
        RETURNS public.user_profiles
        LANGUAGE plpgsql
        AS $$
        DECLARE
            profile public.user_profiles;
        BEGIN
            INSERT INTO public.user_profiles (auth_id, email, full_name, role)
            VALUES (_auth_id, _email, _full_name, public.normalize_profile_role(_role))
            ON CONFLICT (auth_id) DO UPDATE
            SET email = EXCLUDED.email,
                full_name = EXCLUDED.full_name,
                role = EXCLUDED.role,
                updated_at = NOW()
            RETURNING * INTO profile;

            RETURN profile;
        END;
        $$;

        CREATE OR REPLACE FUNCTION public.get_user_profile_by_email(_email TEXT)
        RETURNS SETOF public.user_profiles
        LANGUAGE sql
        STABLE
        AS $$
            SELECT * FROM public.user_profiles WHERE email = _email;
        $$;

        CREATE OR REPLACE FUNCTION public.get_user_profile_by_auth_id(_auth_id UUID)
        RETURNS SETOF public.user_profiles
        LANGUAGE sql
        STABLE
        AS $$
            SELECT * FROM public.user_profiles WHERE auth_id = _auth_id;
        $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF to_regclass('auth.users') IS NOT NULL THEN
                DROP TRIGGER IF EXISTS on_auth_user_created_profile ON auth.users;
                CREATE TRIGGER on_auth_user_created_profile
                AFTER INSERT ON auth.users
                FOR EACH ROW EXECUTE FUNCTION public.handle_new_auth_user_profile();
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_publication WHERE pubname = 'supabase_realtime') THEN
                IF to_regclass('public.agent_logs') IS NOT NULL AND NOT EXISTS (
                    SELECT 1 FROM pg_publication_tables
                    WHERE pubname = 'supabase_realtime'
                      AND schemaname = 'public'
                      AND tablename = 'agent_logs'
                ) THEN
                    ALTER PUBLICATION supabase_realtime ADD TABLE public.agent_logs;
                END IF;
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF to_regclass('auth.users') IS NOT NULL THEN
                DROP TRIGGER IF EXISTS on_auth_user_created_profile ON auth.users;
            END IF;
        END $$;

        DROP FUNCTION IF EXISTS public.handle_new_auth_user_profile();
        DROP FUNCTION IF EXISTS public.register_user_profile(UUID, TEXT, TEXT, TEXT);
        DROP FUNCTION IF EXISTS public.get_user_profile_by_email(TEXT);
        DROP FUNCTION IF EXISTS public.get_user_profile_by_auth_id(UUID);
        DROP FUNCTION IF EXISTS public.normalize_profile_role(TEXT);
        """
    )
