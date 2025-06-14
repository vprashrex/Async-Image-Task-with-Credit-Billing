-- Initialize database if it doesn't exist
-- This script runs when PostgreSQL container starts for the first time

-- Create database (if not exists, handled by POSTGRES_DB env var)
-- CREATE DATABASE IF NOT EXISTS virtual_space_db;

-- You can add any additional initialization SQL here
-- For example, extensions, initial data, etc.

-- Enable UUID extension if needed
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable PostGIS if needed for location features
-- CREATE EXTENSION IF NOT EXISTS postgis;

-- Initial database is created automatically by PostgreSQL container
-- using POSTGRES_DB environment variable
