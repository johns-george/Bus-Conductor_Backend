-- ============================================================
-- Bus Conductor Database Dump
-- Generated: 2026-08-25
-- Database: busconductor (PostgreSQL 17)
-- ============================================================

-- Drop existing tables (order respects foreign keys)
DROP TABLE IF EXISTS payment_methods CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS tickets CASCADE;
DROP TABLE IF EXISTS wallets CASCADE;
DROP TABLE IF EXISTS bus_route CASCADE;
DROP TABLE IF EXISTS route_stop CASCADE;
DROP TABLE IF EXISTS edge CASCADE;
DROP TABLE IF EXISTS bus CASCADE;
DROP TABLE IF EXISTS route CASCADE;
DROP TABLE IF EXISTS stops CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ============================================================
-- TABLE SCHEMAS
-- ============================================================

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL,
    email VARCHAR NOT NULL,
    password_hash VARCHAR,
    full_name VARCHAR,
    role VARCHAR,
    mobile_number VARCHAR,
    google_id VARCHAR(255)
);

CREATE TABLE stops (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(255),
    area VARCHAR(100),
    city VARCHAR(100),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);

CREATE TABLE route (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    start_stop_id BIGINT REFERENCES stops(id),
    end_stop_id BIGINT REFERENCES stops(id)
);

CREATE TABLE edge (
    id BIGSERIAL PRIMARY KEY,
    from_stop BIGINT NOT NULL REFERENCES stops(id),
    to_stop BIGINT NOT NULL REFERENCES stops(id),
    distance DOUBLE PRECISION NOT NULL
);

CREATE TABLE bus (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100),
    bus_number VARCHAR(20),
    bus_type VARCHAR(20) DEFAULT 'non_ac_seater',
    operator_name VARCHAR(100),
    capacity INTEGER DEFAULT 40,
    days VARCHAR(50) DEFAULT '1,2,3,4,5,6,7'
);

CREATE TABLE bus_route (
    id BIGSERIAL PRIMARY KEY,
    bus_id BIGINT NOT NULL REFERENCES bus(id),
    route_id BIGINT NOT NULL REFERENCES route(id),
    start_time TIME NOT NULL,
    platform VARCHAR(10) DEFAULT 'P1',
    days_of_week TEXT DEFAULT 'mon,tue,wed,thu,fri,sat,sun'
);

CREATE TABLE route_stop (
    id BIGSERIAL PRIMARY KEY,
    route_id BIGINT NOT NULL REFERENCES route(id),
    stop_id BIGINT NOT NULL REFERENCES stops(id),
    stop_order INTEGER NOT NULL
);

CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    trip_id INTEGER,
    source_stop_id INTEGER,
    destination_stop_id INTEGER,
    booking_time TIMESTAMP,
    status VARCHAR,
    price DOUBLE PRECISION DEFAULT 0,
    qr_token VARCHAR(512),
    expires_at TIMESTAMP,
    validated_by INTEGER,
    validated_at TIMESTAMP,
    passenger_name VARCHAR(255),
    passenger_phone VARCHAR(20),
    passenger_count INTEGER DEFAULT 1
);

CREATE TABLE wallets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    balance DOUBLE PRECISION,
    currency VARCHAR,
    last_updated TIMESTAMP,
    created_at TIMESTAMP
);

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    wallet_id INTEGER REFERENCES wallets(id),
    amount DOUBLE PRECISION NOT NULL,
    type VARCHAR NOT NULL,
    status VARCHAR,
    payment_method VARCHAR,
    reference_id VARCHAR,
    ticket_id INTEGER REFERENCES tickets(id),
    note VARCHAR,
    method_label VARCHAR,
    payment_id VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE payment_methods (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    method_type VARCHAR(20) NOT NULL,
    label VARCHAR(100) NOT NULL,
    subtitle VARCHAR(200),
    provider VARCHAR(100),
    last_four VARCHAR(4),
    upi_id VARCHAR(100),
    is_default BOOLEAN,
    is_active BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- ============================================================
-- DATA
-- ============================================================

-- ── Users ──────────────────────────────────────────────────
INSERT INTO users (id, username, email, password_hash, full_name, role, mobile_number, google_id) VALUES (1, 'johnsgeorge14', 'johnsgeorge14@gmail.com', '$2b$12$CVdUyLMm8JS6ziW0EorZwe7wAmaKOZdEpWLpwjLUEP/HHIOMpb5ry', 'Johns George', 'USER', '123456789', NULL);
INSERT INTO users (id, username, email, password_hash, full_name, role, mobile_number, google_id) VALUES (2, 'azmi123', 'azmi123@gmail.com', '$2b$12$2pqX19o/Fo.twKiucm6Av.q4K0CstlRYWNUWWAbaWh4U/xMJD/rJa', 'azmi123', 'USER', '12345678', NULL);
INSERT INTO users (id, username, email, password_hash, full_name, role, mobile_number, google_id) VALUES (3, 'shanid123', 'shanid123@gmail.com', '$2b$12$y1j3uDgfBmag/G.406r7IurBmZ4WqSXF50647IB6zcSR5Cg9xcscG', 'shanid', 'USER', '12345678', NULL);
INSERT INTO users (id, username, email, password_hash, full_name, role, mobile_number, google_id) VALUES (4, 'conductor1', 'conductor@bus.com', '$2b$12$Y0ccA0zkwNsA2HfEWUFsGOVHnSKzrAYk9uJrVZuxN3PJgSmq1gOOa', 'Bus Conductor', 'CONDUCTOR', NULL, NULL);
INSERT INTO users (id, username, email, password_hash, full_name, role, mobile_number, google_id) VALUES (5, 'admin1', 'admin@bus.com', '$2b$12$WoXCZDYvWIX0fCNvJQsysudOU7hKC/ad/ZA8J3deDR.6erswR/rHy', 'System Admin', 'USER', NULL, NULL);
INSERT INTO users (id, username, email, password_hash, full_name, role, mobile_number, google_id) VALUES (6, 'shani123', 'shani123@gmail.com', '$2b$12$IKxgTWEUk1kUCZzRIvPv/u1YRxS/.N9KDpHtEUwEJCwJRNPUTNN8C', 'shanid', 'CONDUCTOR', '123456', NULL);
INSERT INTO users (id, username, email, password_hash, full_name, role, mobile_number, google_id) VALUES (7, 'azmi', 'azmi@gmail.com', '$2b$12$UxzNT7E1siXd/ncBYGETi.LPfBevlNFJTOgNOoF/HA/z3u95lxZaG', 'azmi', 'ADMIN', '123456', NULL);

-- ── Stops ──────────────────────────────────────────────────
INSERT INTO stops (id, name, address, area, city, latitude, longitude) VALUES (1, 'Central Bus Station', '123 Main St, Downtown', 'Kakkanad', 'Kochi', 9.9816, 76.2999);
INSERT INTO stops (id, name, address, area, city, latitude, longitude) VALUES (2, 'Airport Terminal', '456 Airport Rd', 'Kakkanad', 'Kochi', 9.9312, 76.2673);
INSERT INTO stops (id, name, address, area, city, latitude, longitude) VALUES (3, 'University Campus', '789 Campus Blvd', 'Kakkanad', 'Kochi', 10.0159, 76.3067);
INSERT INTO stops (id, name, address, area, city, latitude, longitude) VALUES (4, 'Shopping Mall', '321 Mall Ave', 'Edappally', 'Kochi', 10.0268, 76.3075);
INSERT INTO stops (id, name, address, area, city, latitude, longitude) VALUES (5, 'City Hall', '555 Government Plaza', 'Ernakulam', 'Kochi', 9.968, 76.284);
INSERT INTO stops (id, name, address, area, city, latitude, longitude) VALUES (6, 'Tech Park', '888 Innovation Dr', 'Infopark', 'Kochi', 9.9576, 76.3388);
INSERT INTO stops (id, name, address, area, city, latitude, longitude) VALUES (7, 'Hospital Entrance', '999 Medical Center Way', 'Kalamassery', 'Kochi', 9.9937, 76.3388);

-- ── Routes ─────────────────────────────────────────────────
INSERT INTO route (id, name, start_stop_id, end_stop_id) VALUES (1, 'Downtown Express', 1, 2);
INSERT INTO route (id, name, start_stop_id, end_stop_id) VALUES (2, 'Airport Shuttle', 2, 3);
INSERT INTO route (id, name, start_stop_id, end_stop_id) VALUES (3, 'Campus Loop', 3, 4);
INSERT INTO route (id, name, start_stop_id, end_stop_id) VALUES (4, 'Shopping Route', 4, 5);
INSERT INTO route (id, name, start_stop_id, end_stop_id) VALUES (5, 'City Circular', 5, 6);
INSERT INTO route (id, name, start_stop_id, end_stop_id) VALUES (6, 'Central to University Route', 1, 3);
INSERT INTO route (id, name, start_stop_id, end_stop_id) VALUES (7, 'Mall to City Hall Route', 4, 1);

-- ── Edges ──────────────────────────────────────────────────
INSERT INTO edge (id, from_stop, to_stop, distance) VALUES (7, 1, 5, 2.5);
INSERT INTO edge (id, from_stop, to_stop, distance) VALUES (8, 5, 2, 3.1);
INSERT INTO edge (id, from_stop, to_stop, distance) VALUES (9, 2, 6, 4.2);
INSERT INTO edge (id, from_stop, to_stop, distance) VALUES (10, 6, 3, 2.8);
INSERT INTO edge (id, from_stop, to_stop, distance) VALUES (11, 3, 7, 1.9);
INSERT INTO edge (id, from_stop, to_stop, distance) VALUES (12, 7, 4, 2.4);
INSERT INTO edge (id, from_stop, to_stop, distance) VALUES (13, 4, 1, 3.0);
INSERT INTO edge (id, from_stop, to_stop, distance) VALUES (15, 5, 7, 1.5);
INSERT INTO edge (id, from_stop, to_stop, distance) VALUES (16, 7, 6, 4.0);
INSERT INTO edge (id, from_stop, to_stop, distance) VALUES (17, 1, 2, 5.5);
INSERT INTO edge (id, from_stop, to_stop, distance) VALUES (18, 2, 3, 3.5);
INSERT INTO edge (id, from_stop, to_stop, distance) VALUES (19, 4, 5, 2.7);
INSERT INTO edge (id, from_stop, to_stop, distance) VALUES (20, 5, 1, 2.1);

-- ── Buses ──────────────────────────────────────────────────
INSERT INTO bus (id, name, bus_number, bus_type, operator_name, capacity, days) VALUES (1, 'Express Bus 1', 'BUS-001', 'non_ac_seater', 'Default Operator', 40, '1,2,3,4,5,6,7');
INSERT INTO bus (id, name, bus_number, bus_type, operator_name, capacity, days) VALUES (2, 'Airport Shuttle', 'BUS-002', 'non_ac_seater', 'Default Operator', 40, '1,2,3,4,5,6,7');
INSERT INTO bus (id, name, bus_number, bus_type, operator_name, capacity, days) VALUES (3, 'Campus Bus', 'BUS-003', 'non_ac_seater', 'Default Operator', 40, '1,2,3,4,5,6,7');
INSERT INTO bus (id, name, bus_number, bus_type, operator_name, capacity, days) VALUES (4, 'Shopping Route Bus', 'BUS-004', 'non_ac_seater', 'Default Operator', 40, '1,2,3,4,5,6,7');
INSERT INTO bus (id, name, bus_number, bus_type, operator_name, capacity, days) VALUES (5, 'City Circular Bus', 'BUS-005', 'non_ac_seater', 'Default Operator', 40, '1,2,3,4,5,6,7');
INSERT INTO bus (id, name, bus_number, bus_type, operator_name, capacity, days) VALUES (6, 'TEST', 'BUS-006', 'non_ac_seater', 'Default Operator', 40, '1,2,3,4,5,6,7');

-- ── Bus Routes ─────────────────────────────────────────────
INSERT INTO bus_route (id, bus_id, route_id, start_time, platform, days_of_week) VALUES (1, 1, 1, '08:00:00', 'P1', 'mon,tue,wed,thu,fri');
INSERT INTO bus_route (id, bus_id, route_id, start_time, platform, days_of_week) VALUES (2, 2, 2, '09:00:00', 'P1', 'sat,sun');
INSERT INTO bus_route (id, bus_id, route_id, start_time, platform, days_of_week) VALUES (3, 3, 3, '10:00:00', 'P1', 'mon,wed,fri');
INSERT INTO bus_route (id, bus_id, route_id, start_time, platform, days_of_week) VALUES (4, 4, 4, '11:00:00', 'P1', 'tue,thu,sat');
INSERT INTO bus_route (id, bus_id, route_id, start_time, platform, days_of_week) VALUES (5, 5, 5, '12:00:00', 'P1', 'mon,tue,wed,thu,fri,sat,sun');
INSERT INTO bus_route (id, bus_id, route_id, start_time, platform, days_of_week) VALUES (6, 6, 6, '13:00:00', 'P1', 'mon,tue,wed,thu,fri,sat,sun');

-- ── Route Stops ────────────────────────────────────────────
INSERT INTO route_stop (id, route_id, stop_id, stop_order) VALUES (3, 1, 1, 1);
INSERT INTO route_stop (id, route_id, stop_id, stop_order) VALUES (4, 1, 5, 2);
INSERT INTO route_stop (id, route_id, stop_id, stop_order) VALUES (5, 1, 2, 3);
INSERT INTO route_stop (id, route_id, stop_id, stop_order) VALUES (6, 2, 2, 1);
INSERT INTO route_stop (id, route_id, stop_id, stop_order) VALUES (7, 2, 6, 2);
INSERT INTO route_stop (id, route_id, stop_id, stop_order) VALUES (8, 2, 3, 3);
INSERT INTO route_stop (id, route_id, stop_id, stop_order) VALUES (9, 3, 3, 1);
INSERT INTO route_stop (id, route_id, stop_id, stop_order) VALUES (10, 3, 7, 2);
INSERT INTO route_stop (id, route_id, stop_id, stop_order) VALUES (11, 3, 4, 3);
INSERT INTO route_stop (id, route_id, stop_id, stop_order) VALUES (12, 4, 4, 1);
INSERT INTO route_stop (id, route_id, stop_id, stop_order) VALUES (13, 4, 1, 2);
INSERT INTO route_stop (id, route_id, stop_id, stop_order) VALUES (14, 4, 5, 3);
INSERT INTO route_stop (id, route_id, stop_id, stop_order) VALUES (16, 5, 5, 1);
INSERT INTO route_stop (id, route_id, stop_id, stop_order) VALUES (17, 5, 7, 2);
INSERT INTO route_stop (id, route_id, stop_id, stop_order) VALUES (18, 5, 6, 3);
INSERT INTO route_stop (id, route_id, stop_id, stop_order) VALUES (19, 6, 1, 1);
INSERT INTO route_stop (id, route_id, stop_id, stop_order) VALUES (20, 6, 2, 2);
INSERT INTO route_stop (id, route_id, stop_id, stop_order) VALUES (21, 6, 3, 3);
INSERT INTO route_stop (id, route_id, stop_id, stop_order) VALUES (22, 7, 4, 1);
INSERT INTO route_stop (id, route_id, stop_id, stop_order) VALUES (23, 7, 5, 2);
INSERT INTO route_stop (id, route_id, stop_id, stop_order) VALUES (24, 7, 1, 3);

-- ── Tickets ────────────────────────────────────────────────
INSERT INTO tickets (id, user_id, trip_id, source_stop_id, destination_stop_id, booking_time, status, price, qr_token, expires_at, validated_by, validated_at, passenger_name, passenger_phone, passenger_count) VALUES (22, 1, 1, 1, 2, '2026-08-25T08:43:13.016847', 'EXPIRED', 52.0, 'bc.ticket.22.20260825T124313Z.3322181ea2dd5f53', '2026-08-25T12:43:13.016847', NULL, NULL, NULL, NULL, 1);
INSERT INTO tickets (id, user_id, trip_id, source_stop_id, destination_stop_id, booking_time, status, price, qr_token, expires_at, validated_by, validated_at, passenger_name, passenger_phone, passenger_count) VALUES (23, 1, 5, 5, 7, '2026-08-25T16:25:38.172689', 'CANCELLED', 13.0, 'bc.ticket.23.20260825T202538Z.8700eb690ddc8991', '2026-08-25T20:25:38.172689', NULL, NULL, 'Johns George', '123456789', 1);

-- ── Wallets ────────────────────────────────────────────────
INSERT INTO wallets (id, user_id, balance, currency, last_updated, created_at) VALUES (4, 1, 13.0, 'INR', '2026-08-25T16:30:38.053024', '2026-08-24T17:01:26.778524');

-- ── Transactions ───────────────────────────────────────────
INSERT INTO transactions (id, user_id, wallet_id, amount, type, status, payment_method, reference_id, ticket_id, note, method_label, payment_id, created_at, updated_at) VALUES (22, 1, NULL, 52.0, 'BOOKING', 'SUCCESSFUL', 'UPI', 'bk_1DC6A9ED', 22, 'Downtown Express', 'UPI · alex@okhdfc', 'pay_1787647393', '2026-08-25T08:43:13.046208', '2026-08-25T08:43:13.047115');
INSERT INTO transactions (id, user_id, wallet_id, amount, type, status, payment_method, reference_id, ticket_id, note, method_label, payment_id, created_at, updated_at) VALUES (23, 1, NULL, 13.0, 'BOOKING', 'SUCCESSFUL', 'UPI', 'bk_35D10417', 23, 'City Circular', 'UPI · alex@okhdfc', 'pay_1787675138', '2026-08-25T16:25:38.203939', '2026-08-25T16:25:38.205688');
INSERT INTO transactions (id, user_id, wallet_id, amount, type, status, payment_method, reference_id, ticket_id, note, method_label, payment_id, created_at, updated_at) VALUES (24, 1, 4, 13.0, 'REFUND', 'SUCCESSFUL', 'WALLET', NULL, 23, 'Refund for cancelled ticket #23', 'Wallet refund', NULL, '2026-08-25T16:30:38.069015', '2026-08-25T16:30:38.071195');

-- ── Payment Methods ────────────────────────────────────────
INSERT INTO payment_methods (id, user_id, method_type, label, subtitle, provider, last_four, upi_id, is_default, is_active, created_at, updated_at) VALUES (1, 1, 'UPI', 'md', '2345', NULL, NULL, '2345', TRUE, FALSE, '2026-08-24T12:49:19.746574', '2026-08-25T16:32:47.625353');
INSERT INTO payment_methods (id, user_id, method_type, label, subtitle, provider, last_four, upi_id, is_default, is_active, created_at, updated_at) VALUES (2, 1, 'UPI', 'dww', 'dfwfw', NULL, NULL, 'dfwfw', FALSE, FALSE, '2026-08-25T16:32:35.828650', '2026-08-25T16:32:50.118033');

-- ============================================================
-- RESET SEQUENCES
-- ============================================================
SELECT setval('users_id_seq', (SELECT MAX(id) + 1 FROM users));
SELECT setval('stops_id_seq', (SELECT MAX(id) + 1 FROM stops));
SELECT setval('route_id_seq', (SELECT MAX(id) + 1 FROM route));
SELECT setval('edge_id_seq', (SELECT MAX(id) + 1 FROM edge));
SELECT setval('bus_id_seq', (SELECT MAX(id) + 1 FROM bus));
SELECT setval('bus_route_id_seq', (SELECT MAX(id) + 1 FROM bus_route));
SELECT setval('route_stop_id_seq', (SELECT MAX(id) + 1 FROM route_stop));
SELECT setval('tickets_id_seq', (SELECT MAX(id) + 1 FROM tickets));
SELECT setval('wallets_id_seq', (SELECT MAX(id) + 1 FROM wallets));
SELECT setval('transactions_id_seq', (SELECT MAX(id) + 1 FROM transactions));
SELECT setval('payment_methods_id_seq', (SELECT MAX(id) + 1 FROM payment_methods));
