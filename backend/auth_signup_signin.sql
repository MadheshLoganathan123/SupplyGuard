-- ============================================================
-- Auth signup / signin support for SupplyGuard
-- Use this file with Supabase SQL editor or your PostgreSQL database.
-- ============================================================

-- 1. User profile table for storing signup metadata linked to Supabase Auth
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auth_id UUID UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    address TEXT,
    latitude NUMERIC(9, 6),
    longitude NUMERIC(9, 6),
    availability_status TEXT,
    emergency_contact_name TEXT,
    emergency_contact_phone TEXT,
    emergency_contact_relationship TEXT,
    profile_complete BOOLEAN NOT NULL DEFAULT FALSE,
    trust_score NUMERIC(5, 2) NOT NULL DEFAULT 0.0,
    trust_reviews INT NOT NULL DEFAULT 0,
    additional_credentials TEXT,
    role TEXT NOT NULL CHECK (role IN ('admin','farmer','driver','store_owner','pantry_manager','viewer')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.user_profiles IS 'Profile metadata created during signup and linked to Supabase auth users.';
COMMENT ON COLUMN public.user_profiles.auth_id IS 'References auth.users.id from Supabase Auth.';
COMMENT ON COLUMN public.user_profiles.role IS 'Platform roles used during signup.';
COMMENT ON COLUMN public.user_profiles.address IS 'Primary address for the user or service location.';
COMMENT ON COLUMN public.user_profiles.latitude IS 'Location latitude for the user or service location.';
COMMENT ON COLUMN public.user_profiles.longitude IS 'Location longitude for the user or service location.';
COMMENT ON COLUMN public.user_profiles.availability_status IS 'Online / offline / on-duty status for the user.';
COMMENT ON COLUMN public.user_profiles.emergency_contact_name IS 'Emergency contact name for this user.';
COMMENT ON COLUMN public.user_profiles.emergency_contact_phone IS 'Emergency contact phone number.';
COMMENT ON COLUMN public.user_profiles.emergency_contact_relationship IS 'Relationship to emergency contact.';
COMMENT ON COLUMN public.user_profiles.profile_complete IS 'Flag indicating whether the user has completed their profile.';
COMMENT ON COLUMN public.user_profiles.trust_score IS 'Aggregate trust score for the profile based on deliveries and ratings.';
COMMENT ON COLUMN public.user_profiles.trust_reviews IS 'Count of reliability or community reviews for the profile.';

-- 2. Support function to register a new user profile after signup
CREATE OR REPLACE FUNCTION public.register_user_profile(
    _auth_id UUID,
    _email TEXT,
    _full_name TEXT,
    _role TEXT
)
RETURNS public.user_profiles
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    INSERT INTO public.user_profiles (auth_id, email, full_name, role)
    VALUES (_auth_id, _email, _full_name, _role)
    RETURNING *;
END;
$$;

-- 3. Sign-in helper that returns profile details for a given email
CREATE OR REPLACE FUNCTION public.get_user_profile_by_email(
    _email TEXT
)
RETURNS TABLE(
    id UUID,
    auth_id UUID,
    full_name TEXT,
    email TEXT,
    phone TEXT,
    address TEXT,
    latitude NUMERIC(9, 6),
    longitude NUMERIC(9, 6),
    availability_status TEXT,
    emergency_contact_name TEXT,
    emergency_contact_phone TEXT,
    emergency_contact_relationship TEXT,
    profile_complete BOOLEAN,
    trust_score NUMERIC(5, 2),
    trust_reviews INT,
    additional_credentials TEXT,
    role TEXT,
    created_at TIMESTAMPTZ
)
LANGUAGE sql
AS $$
    SELECT id, auth_id, full_name, email, phone, address, latitude, longitude, availability_status,
           emergency_contact_name, emergency_contact_phone, emergency_contact_relationship,
           profile_complete, trust_score, trust_reviews, additional_credentials, role, created_at
    FROM public.user_profiles
    WHERE email = _email;
$$;

CREATE OR REPLACE FUNCTION public.get_user_profile_by_auth_id(
    _auth_id UUID
)
RETURNS TABLE(
    id UUID,
    auth_id UUID,
    full_name TEXT,
    email TEXT,
    phone TEXT,
    address TEXT,
    latitude NUMERIC(9, 6),
    longitude NUMERIC(9, 6),
    availability_status TEXT,
    emergency_contact_name TEXT,
    emergency_contact_phone TEXT,
    emergency_contact_relationship TEXT,
    profile_complete BOOLEAN,
    trust_score NUMERIC(5, 2),
    trust_reviews INT,
    additional_credentials TEXT,
    role TEXT,
    created_at TIMESTAMPTZ
)
LANGUAGE sql
AS $$
    SELECT id, auth_id, full_name, email, phone, address, latitude, longitude, availability_status,
           emergency_contact_name, emergency_contact_phone, emergency_contact_relationship,
           profile_complete, trust_score, trust_reviews, additional_credentials, role, created_at
    FROM public.user_profiles
    WHERE auth_id = _auth_id;
$$;

CREATE OR REPLACE FUNCTION public.update_user_profile(
    _auth_id UUID,
    _email TEXT,
    _full_name TEXT,
    _phone TEXT,
    _address TEXT,
    _latitude NUMERIC(9, 6),
    _longitude NUMERIC(9, 6),
    _availability_status TEXT,
    _emergency_contact_name TEXT,
    _emergency_contact_phone TEXT,
    _emergency_contact_relationship TEXT,
    _profile_complete BOOLEAN,
    _additional_credentials TEXT,
    _role TEXT
)
RETURNS public.user_profiles
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    INSERT INTO public.user_profiles (
        auth_id, email, full_name, phone, address, latitude, longitude,
        availability_status, emergency_contact_name, emergency_contact_phone,
        emergency_contact_relationship, profile_complete, additional_credentials, role
    ) VALUES (
        _auth_id, _email, _full_name, _phone, _address, _latitude, _longitude,
        _availability_status, _emergency_contact_name, _emergency_contact_phone,
        _emergency_contact_relationship, _profile_complete, _additional_credentials, _role
    )
    ON CONFLICT (auth_id) DO UPDATE
    SET
        email = EXCLUDED.email,
        full_name = EXCLUDED.full_name,
        phone = EXCLUDED.phone,
        address = EXCLUDED.address,
        latitude = EXCLUDED.latitude,
        longitude = EXCLUDED.longitude,
        availability_status = EXCLUDED.availability_status,
        emergency_contact_name = EXCLUDED.emergency_contact_name,
        emergency_contact_phone = EXCLUDED.emergency_contact_phone,
        emergency_contact_relationship = EXCLUDED.emergency_contact_relationship,
        profile_complete = EXCLUDED.profile_complete,
        additional_credentials = EXCLUDED.additional_credentials,
        role = EXCLUDED.role,
        updated_at = NOW()
    RETURNING *;
END;
$$;

-- 4. Example signup usage:
-- SELECT public.register_user_profile('AUTH_USER_ID', 'user@example.com', 'User Name', 'farmer');

-- 5. Example signin lookup usage:
-- SELECT * FROM public.get_user_profile_by_email('user@example.com');
