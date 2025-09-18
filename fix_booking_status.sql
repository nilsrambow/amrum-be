-- Fix booking status values to match the enum
-- Run this SQL directly in your database if you have incorrect values

UPDATE bookings SET status = 'NEW' WHERE status = 'new';
UPDATE bookings SET status = 'CONFIRMED' WHERE status = 'confirmed';
UPDATE bookings SET status = 'KURKARTEN_REQUESTED' WHERE status = 'kurkarten_requested';
UPDATE bookings SET status = 'READY_FOR_ARRIVAL' WHERE status = 'ready_for_arrival';
UPDATE bookings SET status = 'ARRIVING' WHERE status = 'arriving';
UPDATE bookings SET status = 'ON_SITE' WHERE status = 'on_site';
UPDATE bookings SET status = 'DEPARTING' WHERE status = 'departing';
UPDATE bookings SET status = 'DEPARTED_READINGS_DUE' WHERE status = 'departed_readings_due';

-- Set any NULL values to NEW
UPDATE bookings SET status = 'NEW' WHERE status IS NULL; 