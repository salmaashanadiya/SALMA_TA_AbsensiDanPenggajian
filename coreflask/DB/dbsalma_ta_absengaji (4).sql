-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Waktu pembuatan: 30 Apr 2026 pada 05.04
-- Versi server: 10.4.32-MariaDB
-- Versi PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `dbsalma_ta_absengaji`
--

-- --------------------------------------------------------

--
-- Struktur dari tabel `absensi_salma`
--

CREATE TABLE `absensi_salma` (
  `id_absensi_salma` int(11) NOT NULL,
  `id_user_salma` varchar(10) NOT NULL,
  `tanggal_absensi_salma` date NOT NULL,
  `jam_masuk_salma` time DEFAULT NULL,
  `jam_pulang_salma` time DEFAULT NULL,
  `status_absensi_salma` enum('hadir','izin','sakit','alpha') DEFAULT 'hadir',
  `keterangan_salma` varchar(100) DEFAULT NULL,
  `created_at_salma` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `absensi_salma`
--

INSERT INTO `absensi_salma` (`id_absensi_salma`, `id_user_salma`, `tanggal_absensi_salma`, `jam_masuk_salma`, `jam_pulang_salma`, `status_absensi_salma`, `keterangan_salma`, `created_at_salma`) VALUES
(1, 'KR001', '2026-01-02', '07:55:00', '16:10:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(2, 'KR001', '2026-01-05', '08:05:00', '16:20:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(3, 'KR001', '2026-01-06', '07:50:00', '16:05:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(4, 'KR001', '2026-01-07', '08:15:00', '16:30:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(5, 'KR001', '2026-01-08', '07:45:00', '16:00:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(6, 'KR001', '2026-01-09', '08:00:00', '17:10:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(7, 'KR001', '2026-01-12', '08:10:00', '16:25:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(8, 'KR001', '2026-01-13', '07:55:00', '16:15:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(9, 'KR001', '2026-01-14', '08:20:00', '16:40:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(10, 'KR001', '2026-01-15', '07:50:00', '16:05:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(11, 'KR001', '2026-01-16', '08:05:00', '17:00:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(12, 'KR001', '2026-01-19', '07:45:00', '16:00:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(13, 'KR001', '2026-01-20', '08:15:00', '16:35:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(14, 'KR001', '2026-01-21', '07:55:00', '16:10:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(15, 'KR001', '2026-01-22', '08:00:00', '16:20:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(16, 'KR001', '2026-01-23', '08:10:00', '17:15:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(17, 'KR001', '2026-01-26', '07:50:00', '16:05:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(18, 'KR001', '2026-01-27', '08:20:00', '16:45:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(19, 'KR001', '2026-01-28', '07:55:00', '16:10:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(21, 'KR001', '2026-01-30', '08:00:00', '17:20:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(22, 'KR001', '2026-02-02', '07:50:00', '16:05:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(23, 'KR001', '2026-02-03', '08:10:00', '16:25:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(24, 'KR001', '2026-02-04', '07:55:00', '16:10:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(25, 'KR001', '2026-02-05', '08:20:00', '16:40:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(26, 'KR001', '2026-02-06', '08:00:00', '17:10:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(27, 'KR001', '2026-02-09', '07:45:00', '16:00:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(28, 'KR001', '2026-02-10', '08:15:00', '16:30:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(29, 'KR001', '2026-02-11', '07:50:00', '16:05:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(30, 'KR001', '2026-02-12', '08:05:00', '16:20:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(31, 'KR001', '2026-02-13', '08:10:00', '17:00:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(32, 'KR001', '2026-02-16', '07:55:00', '16:10:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(34, 'KR001', '2026-02-18', '07:50:00', '16:05:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(35, 'KR001', '2026-02-19', '08:00:00', '16:20:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(36, 'KR001', '2026-02-20', '08:15:00', '17:15:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(37, 'KR001', '2026-02-23', '07:45:00', '16:00:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(38, 'KR001', '2026-02-24', '08:10:00', '16:25:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(39, 'KR001', '2026-02-25', '07:55:00', '16:10:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(40, 'KR001', '2026-02-26', '08:05:00', '16:30:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(41, 'KR001', '2026-02-27', '08:00:00', '17:20:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(42, 'KR001', '2026-03-02', '07:50:00', '16:05:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(43, 'KR001', '2026-03-03', '08:10:00', '16:25:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(44, 'KR001', '2026-03-04', '07:55:00', '16:10:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(45, 'KR001', '2026-03-05', '08:20:00', '16:40:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(46, 'KR001', '2026-03-06', '08:00:00', '17:10:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(47, 'KR001', '2026-03-09', '07:45:00', '16:00:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(48, 'KR001', '2026-03-10', '08:15:00', '16:30:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(49, 'KR001', '2026-03-11', '07:50:00', '16:05:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(50, 'KR001', '2026-03-12', '08:05:00', '16:20:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(51, 'KR001', '2026-03-13', '08:10:00', '17:00:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(52, 'KR001', '2026-03-16', '07:55:00', '16:10:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(53, 'KR001', '2026-03-17', '08:20:00', '16:45:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(54, 'KR001', '2026-03-18', '07:50:00', '16:05:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(55, 'KR001', '2026-03-19', '08:00:00', '16:20:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(56, 'KR001', '2026-03-20', '08:15:00', '17:15:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(57, 'KR001', '2026-03-23', '07:45:00', '16:00:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(58, 'KR001', '2026-03-24', '08:10:00', '16:25:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(59, 'KR001', '2026-03-25', '07:55:00', '16:10:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(60, 'KR001', '2026-03-26', '08:05:00', '16:30:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(61, 'KR001', '2026-03-27', '08:00:00', '17:20:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(67, 'KR001', '2026-04-06', '08:05:00', '16:20:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(68, 'KR001', '2026-04-07', '07:45:00', '16:00:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(69, 'KR001', '2026-04-08', '08:15:00', '16:30:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(70, 'KR001', '2026-04-09', NULL, NULL, 'alpha', NULL, '2026-04-22 14:04:25'),
(71, 'KR001', '2026-04-10', '08:00:00', '17:10:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(72, 'KR001', '2026-04-13', '07:55:00', '16:10:00', 'hadir', NULL, '2026-04-22 14:04:25'),
(73, 'KR001', '2026-04-14', NULL, NULL, 'alpha', NULL, '2026-04-22 14:04:25'),
(74, 'KR001', '2026-04-15', NULL, NULL, 'alpha', NULL, '2026-04-22 14:04:25'),
(75, 'KR001', '2026-04-16', '08:05:00', '16:25:00', 'sakit', NULL, '2026-04-22 14:04:25'),
(76, 'KR001', '2026-04-17', '08:10:00', '17:15:00', 'sakit', NULL, '2026-04-22 14:04:25'),
(77, 'KR001', '2026-04-20', '07:45:00', '16:00:00', 'sakit', NULL, '2026-04-22 14:04:25'),
(78, 'KR001', '2026-04-21', NULL, NULL, 'sakit', NULL, '2026-04-22 14:04:25'),
(81, 'KR002', '2026-04-22', '21:11:12', '21:11:29', 'hadir', NULL, '2026-04-22 14:11:12'),
(83, 'KR001', '2026-04-22', NULL, NULL, 'alpha', NULL, '2026-04-22 14:12:50'),
(90, 'KR002', '2026-04-23', NULL, NULL, 'alpha', NULL, '2026-04-23 14:13:29'),
(91, 'KR001', '2026-04-23', NULL, NULL, 'sakit', NULL, '2026-04-23 14:13:38'),
(92, 'KR001', '2026-04-25', NULL, NULL, 'alpha', NULL, '2026-04-25 07:08:06'),
(93, 'KR001', '2026-04-26', NULL, NULL, 'sakit', NULL, '2026-04-25 07:14:51'),
(94, 'KR001', '2026-04-27', NULL, NULL, 'sakit', NULL, '2026-04-25 07:14:51'),
(95, 'KR001', '2026-04-28', NULL, NULL, 'sakit', NULL, '2026-04-25 07:14:51'),
(96, 'KR001', '2026-04-29', NULL, NULL, 'izin', NULL, '2026-04-25 07:14:51'),
(97, 'KR001', '2026-04-30', NULL, NULL, 'sakit', NULL, '2026-04-25 07:14:51'),
(104, 'KR002', '2026-04-27', NULL, NULL, 'alpha', NULL, '2026-04-29 14:00:28'),
(105, 'KR002', '2026-04-28', NULL, NULL, 'alpha', NULL, '2026-04-29 14:00:28'),
(106, 'KR002', '2026-04-29', NULL, NULL, 'alpha', NULL, '2026-04-29 14:00:28'),
(108, 'KR002', '2026-04-26', NULL, NULL, 'alpha', NULL, '2026-04-29 14:36:27'),
(109, 'KR002', '2026-04-20', NULL, NULL, 'alpha', NULL, '2026-04-29 14:44:31'),
(110, 'KR002', '2026-04-30', NULL, NULL, 'alpha', NULL, '2026-04-30 01:30:00'),
(111, 'KR003', '2026-04-30', NULL, NULL, 'alpha', NULL, '2026-04-30 01:30:00'),
(112, 'KR002', '2026-04-14', NULL, NULL, 'alpha', NULL, '2026-04-30 01:36:10'),
(113, 'KR002', '2026-04-09', NULL, NULL, 'alpha', NULL, '2026-04-30 01:36:19'),
(114, 'KR002', '2026-04-07', NULL, NULL, 'alpha', NULL, '2026-04-30 01:36:32'),
(115, 'KR001', '2026-04-18', NULL, NULL, 'sakit', NULL, '2026-04-30 01:56:58'),
(116, 'KR001', '2026-04-19', NULL, NULL, 'sakit', NULL, '2026-04-30 01:56:58'),
(117, 'KR001', '2026-04-01', NULL, NULL, 'sakit', NULL, '2026-04-30 02:31:45'),
(118, 'KR001', '2026-04-03', NULL, NULL, 'alpha', NULL, '2026-04-30 02:35:01');

-- --------------------------------------------------------

--
-- Struktur dari tabel `bonus_template_salma`
--

CREATE TABLE `bonus_template_salma` (
  `id_bonus_template` int(11) NOT NULL,
  `nama_bonus_salma` varchar(100) NOT NULL,
  `tipe_bonus_salma` enum('nominal','persen_gaji_harian','persen_gaji_bulanan','per_jam') DEFAULT NULL,
  `nilai_bonus_salma` decimal(15,2) NOT NULL DEFAULT 0.00,
  `keterangan_salma` varchar(255) DEFAULT NULL,
  `aktif_salma` tinyint(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `bonus_template_salma`
--

INSERT INTO `bonus_template_salma` (`id_bonus_template`, `nama_bonus_salma`, `tipe_bonus_salma`, `nilai_bonus_salma`, `keterangan_salma`, `aktif_salma`) VALUES
(1, 'Bonus Lembur', 'per_jam', 150000.00, '150% dari gaji per hari', 1),
(2, 'Bonus Kehadiran Penuh', 'persen_gaji_bulanan', 10.00, '10% dari total gaji pokok bulan ini', 1),
(3, 'Bonus Kinerja', 'persen_gaji_bulanan', 15.00, '15% dari total gaji pokok bulan ini', 1),
(4, 'Bonus THR', 'persen_gaji_bulanan', 100.00, '1 bulan gaji penuh', 1),
(5, 'Bonus Nominal Tetap', 'nominal', 500000.00, 'Bonus tambahan Rp 500.000', 1);

-- --------------------------------------------------------

--
-- Struktur dari tabel `gaji_salma`
--

CREATE TABLE `gaji_salma` (
  `id_gaji_salma` int(11) NOT NULL,
  `id_user_salma` varchar(10) NOT NULL,
  `tahun_gaji_salma` year(4) NOT NULL,
  `bulan_gaji_salma` tinyint(4) NOT NULL CHECK (`bulan_gaji_salma` between 1 and 12),
  `gaji_pokok_salma` decimal(12,2) NOT NULL,
  `bonus_salma` decimal(12,2) DEFAULT 0.00,
  `detail_bonus_salma` text DEFAULT NULL,
  `potongan_salma` decimal(12,2) DEFAULT 0.00,
  `detail_potongan_salma` text DEFAULT NULL,
  `total_gaji_salma` decimal(12,2) GENERATED ALWAYS AS (`gaji_pokok_salma` + `bonus_salma` - `potongan_salma`) STORED,
  `status_gaji_salma` enum('belum_dibayar','sudah_dibayar') DEFAULT 'belum_dibayar',
  `tanggal_pembayaran_salma` date DEFAULT NULL,
  `created_at_salma` timestamp NOT NULL DEFAULT current_timestamp(),
  `potongan_alpha_salma` decimal(15,2) DEFAULT 0.00,
  `potongan_sakit_salma` decimal(15,2) DEFAULT 0.00,
  `potongan_izin_salma` decimal(15,2) DEFAULT 0.00
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `gaji_salma`
--

INSERT INTO `gaji_salma` (`id_gaji_salma`, `id_user_salma`, `tahun_gaji_salma`, `bulan_gaji_salma`, `gaji_pokok_salma`, `bonus_salma`, `detail_bonus_salma`, `potongan_salma`, `detail_potongan_salma`, `status_gaji_salma`, `tanggal_pembayaran_salma`, `created_at_salma`, `potongan_alpha_salma`, `potongan_sakit_salma`, `potongan_izin_salma`) VALUES
(9, 'KR001', '2026', 1, 10000000.00, 300000.00, 'Bonus kehadiran + lembur', 250000.00, 'BPJS + telat', 'sudah_dibayar', '2026-04-22', '2026-04-22 14:35:52', 0.00, 0.00, 0.00),
(10, 'KR001', '2026', 2, 10000000.00, 200000.00, 'Bonus kehadiran', 350000.00, 'BPJS + izin', 'sudah_dibayar', '2026-04-22', '2026-04-22 14:35:52', 0.00, 0.00, 0.00),
(11, 'KR001', '2026', 3, 10000000.00, 500000.00, 'Bonus lembur', 300000.00, 'BPJS + pajak', 'sudah_dibayar', '2026-04-22', '2026-04-22 14:35:52', 0.00, 0.00, 0.00),
(13, 'KR001', '2026', 4, 6000000.00, 900000.00, NULL, 1175000.00, NULL, 'sudah_dibayar', '2026-04-30', '2026-04-25 07:39:10', 1000000.00, 125000.00, 50000.00);

-- --------------------------------------------------------

--
-- Struktur dari tabel `hari_libur_salma`
--

CREATE TABLE `hari_libur_salma` (
  `id_libur_salma` int(11) NOT NULL,
  `tanggal_libur_salma` date NOT NULL,
  `keterangan_libur_salma` varchar(100) NOT NULL,
  `created_at_salma` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `hari_libur_salma`
--

INSERT INTO `hari_libur_salma` (`id_libur_salma`, `tanggal_libur_salma`, `keterangan_libur_salma`, `created_at_salma`) VALUES
(1, '2026-01-01', 'Tahun Baru 2026', '2026-04-06 04:52:42'),
(2, '2026-01-29', 'Tahun Baru Imlek', '2026-04-06 04:52:42'),
(3, '2026-02-17', 'Isra Miraj', '2026-04-06 04:52:42'),
(4, '2026-03-22', 'Hari Raya Nyepi', '2026-04-06 04:52:42'),
(5, '2026-03-30', 'Idul Fitri 1447 H', '2026-04-06 04:52:42'),
(6, '2026-03-31', 'Idul Fitri 1447 H', '2026-04-06 04:52:42'),
(7, '2026-04-01', 'Cuti Bersama Idul Fitri', '2026-04-06 04:52:42'),
(8, '2026-04-02', 'Cuti Bersama Idul Fitri', '2026-04-06 04:52:42'),
(9, '2026-04-03', 'Wafat Isa Al Masih', '2026-04-06 04:52:42'),
(10, '2026-05-01', 'Hari Buruh Internasional', '2026-04-06 04:52:42'),
(11, '2026-05-14', 'Kenaikan Isa Al Masih', '2026-04-06 04:52:42'),
(12, '2026-05-24', 'Hari Raya Waisak', '2026-04-06 04:52:42'),
(13, '2026-06-01', 'Hari Lahir Pancasila', '2026-04-06 04:52:42'),
(14, '2026-06-06', 'Idul Adha 1447 H', '2026-04-06 04:52:42'),
(15, '2026-06-26', 'Tahun Baru Islam 1448 H', '2026-04-06 04:52:42'),
(16, '2026-08-17', 'Hari Kemerdekaan RI', '2026-04-06 04:52:42'),
(17, '2026-09-04', 'Maulid Nabi Muhammad SAW', '2026-04-06 04:52:42'),
(18, '2026-12-25', 'Hari Raya Natal', '2026-04-06 04:52:42');

-- --------------------------------------------------------

--
-- Struktur dari tabel `izin_salma`
--

CREATE TABLE `izin_salma` (
  `id_izin_salma` int(11) NOT NULL,
  `id_user_salma` varchar(10) NOT NULL,
  `tanggal_mulai_salma` date NOT NULL,
  `tanggal_selesai_salma` date NOT NULL,
  `jenis_izin_salma` enum('izin','sakit','cuti') NOT NULL,
  `alasan_izin_salma` text DEFAULT NULL,
  `foto_bukti_salma` varchar(255) DEFAULT NULL,
  `status_izin_salma` enum('pending','disetujui','ditolak') DEFAULT 'pending',
  `alasan_tolak_salma` text DEFAULT NULL,
  `created_at_salma` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `izin_salma`
--

INSERT INTO `izin_salma` (`id_izin_salma`, `id_user_salma`, `tanggal_mulai_salma`, `tanggal_selesai_salma`, `jenis_izin_salma`, `alasan_izin_salma`, `foto_bukti_salma`, `status_izin_salma`, `alasan_tolak_salma`, `created_at_salma`) VALUES
(1, 'KR001', '2026-04-23', '2026-04-27', 'izin', 'hg', NULL, 'ditolak', 'Otomatis ditolak: kuota izin Anda untuk bulan ini sudah habis (limit 2 hari, sudah terpakai 0 hari).', '2026-04-23 03:33:28'),
(2, 'KR001', '2026-04-23', '2026-04-27', 'sakit', 'h', NULL, 'ditolak', 'Otomatis ditolak: kuota sakit Anda untuk bulan ini sudah habis (limit 3 hari, sudah terpakai 0 hari).', '2026-04-23 03:33:50'),
(3, 'KR001', '2026-04-29', '2026-04-29', 'izin', 'kakak saya menikah', 'KR001_20260429085342.png', 'disetujui', NULL, '2026-04-29 01:53:42');

-- --------------------------------------------------------

--
-- Struktur dari tabel `jabatan_salma`
--

CREATE TABLE `jabatan_salma` (
  `id_jabatan_salma` int(11) NOT NULL,
  `nama_jabatan_salma` varchar(50) DEFAULT NULL,
  `gaji_per_hari_salma` int(11) DEFAULT NULL,
  `tunjangan_salma` int(11) DEFAULT 0,
  `limit_izin_salma` int(11) DEFAULT 2 COMMENT 'Maks hari izin per bulan',
  `limit_sakit_salma` int(11) DEFAULT 3 COMMENT 'Maks hari sakit per bulan',
  `limit_cuti_salma` int(11) DEFAULT 12 COMMENT 'Maks hari cuti per tahun'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `jabatan_salma`
--

INSERT INTO `jabatan_salma` (`id_jabatan_salma`, `nama_jabatan_salma`, `gaji_per_hari_salma`, `tunjangan_salma`, `limit_izin_salma`, `limit_sakit_salma`, `limit_cuti_salma`) VALUES
(1, 'Manager', 500000, 2000000, 2, 3, 12),
(2, 'Supervisor', 350000, 1500000, 2, 3, 12),
(3, 'Admin', 250000, 1000000, 2, 3, 12),
(4, 'Staff', 200000, 800000, 2, 3, 12),
(5, 'Resepsionis', 180000, 600000, 2, 3, 12),
(6, 'Magang', 100000, 500000, 2, 3, 12);

-- --------------------------------------------------------

--
-- Struktur dari tabel `jam_absen_salma`
--

CREATE TABLE `jam_absen_salma` (
  `id` int(11) NOT NULL,
  `jam_masuk_mulai` time NOT NULL DEFAULT '07:00:00',
  `jam_masuk_selesai` time NOT NULL DEFAULT '09:00:00',
  `jam_pulang_mulai` time NOT NULL DEFAULT '16:00:00',
  `jam_pulang_selesai` time NOT NULL DEFAULT '20:00:00',
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `pengajuan_khusus_salma`
--

CREATE TABLE `pengajuan_khusus_salma` (
  `id_khusus` int(11) NOT NULL,
  `id_user_salma` varchar(10) NOT NULL,
  `jenis_izin_salma` enum('izin','sakit') NOT NULL,
  `tanggal_mulai_salma` date NOT NULL,
  `tanggal_selesai_salma` date NOT NULL,
  `alasan_izin_salma` text NOT NULL,
  `alasan_khusus_salma` text NOT NULL COMMENT 'Alasan mengapa mengajukan khusus melebihi batas',
  `foto_bukti_salma` varchar(255) DEFAULT NULL,
  `status_khusus` enum('pending','disetujui','ditolak') DEFAULT 'pending',
  `alasan_tolak_salma` text DEFAULT NULL,
  `created_at_salma` datetime DEFAULT current_timestamp(),
  `updated_at_salma` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `pengajuan_khusus_salma`
--

INSERT INTO `pengajuan_khusus_salma` (`id_khusus`, `id_user_salma`, `jenis_izin_salma`, `tanggal_mulai_salma`, `tanggal_selesai_salma`, `alasan_izin_salma`, `alasan_khusus_salma`, `foto_bukti_salma`, `status_khusus`, `alasan_tolak_salma`, `created_at_salma`, `updated_at_salma`) VALUES
(1, 'KR001', 'sakit', '2026-04-25', '2026-04-30', 'ffjfhfiff', 'fhfhfgdhfgugfsd', NULL, 'disetujui', NULL, '2026-04-25 14:07:25', '2026-04-25 14:14:51'),
(2, 'KR001', 'sakit', '2026-04-16', '2026-04-23', 'trrt', 'uuy', NULL, 'disetujui', NULL, '2026-04-30 08:56:36', '2026-04-30 08:56:58');

-- --------------------------------------------------------

--
-- Struktur dari tabel `potongan_template_salma`
--

CREATE TABLE `potongan_template_salma` (
  `id_potongan_template` int(11) NOT NULL,
  `nama_potongan_salma` varchar(100) NOT NULL,
  `tipe_potongan_salma` enum('persen_gaji_harian','persen_gaji_bulanan','nominal') NOT NULL,
  `nilai_potongan_salma` decimal(15,2) NOT NULL DEFAULT 0.00,
  `keterangan_salma` varchar(255) DEFAULT NULL,
  `aktif_salma` tinyint(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `potongan_template_salma`
--

INSERT INTO `potongan_template_salma` (`id_potongan_template`, `nama_potongan_salma`, `tipe_potongan_salma`, `nilai_potongan_salma`, `keterangan_salma`, `aktif_salma`) VALUES
(1, 'BPJS Kesehatan', 'persen_gaji_bulanan', 1.00, '1% dari gaji pokok (iuran karyawan)', 1),
(2, 'BPJS Ketenagakerjaan', 'persen_gaji_bulanan', 2.00, '2% dari gaji pokok (Jaminan Pensiun)', 1),
(3, 'PPh 21', 'persen_gaji_bulanan', 5.00, '5% pajak penghasilan', 1),
(4, 'Kasbon / Pinjaman', 'nominal', 200000.00, 'Cicilan kasbon Rp 200.000', 1),
(5, 'Keterlambatan', 'persen_gaji_harian', 50.00, '50% dari gaji per hari (per kejadian terlambat)', 1);

-- --------------------------------------------------------

--
-- Struktur dari tabel `request_admin_salma`
--

CREATE TABLE `request_admin_salma` (
  `id_request` int(11) NOT NULL,
  `nama` varchar(100) DEFAULT NULL,
  `jabatan` varchar(100) DEFAULT NULL,
  `username_akun` varchar(100) DEFAULT NULL,
  `jenis_request` enum('belum_akun','lupa_password') DEFAULT NULL,
  `pesan_tambahan` text DEFAULT NULL,
  `status_request` enum('menunggu','dibuka','diproses','selesai') NOT NULL DEFAULT 'menunggu',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `kode_tiket` varchar(30) DEFAULT NULL,
  `catatan_admin` text DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `nama_bank` varchar(100) DEFAULT NULL,
  `no_rekening` varchar(50) DEFAULT NULL,
  `atas_nama_rekening` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `request_admin_salma`
--

INSERT INTO `request_admin_salma` (`id_request`, `nama`, `jabatan`, `username_akun`, `jenis_request`, `pesan_tambahan`, `status_request`, `created_at`, `kode_tiket`, `catatan_admin`, `updated_at`, `nama_bank`, `no_rekening`, `atas_nama_rekening`) VALUES
(4, 'Aruby Shaquilla', 'MAnager', NULL, 'belum_akun', '-', 'selesai', '2026-04-23 03:38:28', 'TKT-20260423-8121', NULL, '2026-04-23 10:39:51', NULL, NULL, NULL),
(5, 'Cleo Mahrezkha Rahza', 'Magang', NULL, 'belum_akun', NULL, 'diproses', '2026-04-29 01:50:42', 'TKT-20260429-2653', NULL, '2026-04-29 09:24:42', NULL, NULL, NULL),
(6, 'Aruby Shaquilla', 'Supervisor', 'arbyshaquil', 'lupa_password', NULL, 'diproses', '2026-04-29 01:52:32', 'TKT-20260429-8066', NULL, '2026-04-29 10:18:38', NULL, NULL, NULL);

-- --------------------------------------------------------

--
-- Struktur dari tabel `response_admin_salma`
--

CREATE TABLE `response_admin_salma` (
  `id` int(11) NOT NULL,
  `request_id` int(11) DEFAULT NULL,
  `pesan` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `rfid_kartu_salma`
--

CREATE TABLE `rfid_kartu_salma` (
  `id_kartu` varchar(50) NOT NULL,
  `id_user_salma` varchar(20) NOT NULL,
  `keterangan` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `rfid_kartu_salma`
--

INSERT INTO `rfid_kartu_salma` (`id_kartu`, `id_user_salma`, `keterangan`) VALUES
('0001461705', 'KR002', 'Kartu Utama'),
('0001707462', 'KR001', 'Kartu Utama');

-- --------------------------------------------------------

--
-- Struktur dari tabel `slip_gaji_salma`
--

CREATE TABLE `slip_gaji_salma` (
  `id_slip_gaji_salma` int(11) NOT NULL,
  `id_gaji_salma` int(11) NOT NULL,
  `nomor_slip_salma` varchar(50) NOT NULL,
  `tanggal_cetak_salma` date NOT NULL,
  `total_diterima_salma` decimal(12,2) NOT NULL,
  `metode_pembayaran_salma` enum('tunai','transfer') DEFAULT 'transfer',
  `catatan_salma` text DEFAULT NULL,
  `created_at_salma` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `surat_peringatan_salma`
--

CREATE TABLE `surat_peringatan_salma` (
  `id_sp` int(11) NOT NULL,
  `id_user_salma` varchar(10) NOT NULL,
  `level_sp` tinyint(4) NOT NULL COMMENT '1=SP1, 2=SP2, 3=SP3',
  `total_alpha` int(11) NOT NULL COMMENT 'Total alpha saat SP diterbitkan',
  `status_sp` enum('menunggu_admin','dikirim','direspon','tidak_direspon') NOT NULL DEFAULT 'menunggu_admin',
  `foto_bukti_sp` varchar(255) DEFAULT NULL,
  `tanggal_respon` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `dikirim_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `surat_peringatan_salma`
--

INSERT INTO `surat_peringatan_salma` (`id_sp`, `id_user_salma`, `level_sp`, `total_alpha`, `status_sp`, `foto_bukti_sp`, `tanggal_respon`, `created_at`, `dikirim_at`) VALUES
(1, 'KR002', 1, 4, 'dikirim', NULL, NULL, '2026-04-29 21:36:27', '2026-04-30 08:15:36'),
(2, 'KR002', 2, 6, 'dikirim', NULL, NULL, '2026-04-29 21:44:31', '2026-04-30 08:35:33'),
(3, 'KR002', 3, 9, 'direspon', 'sp3_KR002_20260430083727.png', '2026-04-30 08:37:27', '2026-04-30 08:36:19', '2026-04-30 08:36:45'),
(4, 'KR001', 1, 3, 'dikirim', NULL, NULL, '2026-04-30 08:52:34', '2026-04-30 09:00:04'),
(5, 'KR001', 2, 6, 'dikirim', NULL, NULL, '2026-04-30 09:35:01', '2026-04-30 09:35:12');

-- --------------------------------------------------------

--
-- Struktur dari tabel `users_salma`
--

CREATE TABLE `users_salma` (
  `id_user_salma` varchar(10) NOT NULL,
  `username_salma` varchar(50) NOT NULL,
  `email_salma` varchar(100) NOT NULL,
  `nama_bank_salma` varchar(50) DEFAULT NULL,
  `no_rekening_salma` varchar(30) DEFAULT NULL,
  `atas_nama_salma` varchar(100) DEFAULT NULL,
  `password_salma` varchar(255) NOT NULL,
  `nama_salma` varchar(100) NOT NULL,
  `nip_salma` varchar(20) NOT NULL,
  `role_salma` enum('admin','karyawan') DEFAULT 'karyawan',
  `status_user_salma` enum('aktif','nonaktif') DEFAULT 'aktif',
  `created_at_salma` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at_salma` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `id_jabatan_salma` int(11) DEFAULT NULL,
  `foto_profil_salma` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `users_salma`
--

INSERT INTO `users_salma` (`id_user_salma`, `username_salma`, `email_salma`, `nama_bank_salma`, `no_rekening_salma`, `atas_nama_salma`, `password_salma`, `nama_salma`, `nip_salma`, `role_salma`, `status_user_salma`, `created_at_salma`, `updated_at_salma`, `id_jabatan_salma`, `foto_profil_salma`) VALUES
('AD001', 'AD001', 'salmaashanadiya@gmail.com', 'BCA', '1776655443322', 'SALMA ASHANADIYA', '123456', 'Salma Ashanadiya', '2987654321', 'admin', 'aktif', '2026-04-18 08:42:50', '2026-04-29 02:38:30', 3, NULL),
('KR001', 'KR001', 'rehan.fdlansyah@gmail.com', 'BCA', '112233445566', 'RAIHAN FADLANSYAH', '098765', 'Raihan Fadlansyah', '2976543456', 'karyawan', 'aktif', '2026-04-18 08:46:52', '2026-04-29 02:38:30', 1, 'user_KR001_1776953136.jpeg'),
('KR002', 'KR002', 'arubyshaquilla@gmail.com', 'BCA', '33344455566', 'ARUBY SHAQUILLA', '123123', 'Aruby Shaquilla', '9298465322', 'karyawan', 'aktif', '2026-04-22 07:04:54', '2026-04-29 02:38:30', 2, NULL),
('KR003', 'KR003', 'cleomhrzha@gmail.com', 'Mandri', '375873726434', 'CLEO MAREZKHA RAHZA', 'KR003', 'Cleo Mahrezkha Rahza', '987232234537', 'karyawan', 'aktif', '2026-04-29 02:26:07', '2026-04-29 02:36:37', 6, NULL);

--
-- Indexes for dumped tables
--

--
-- Indeks untuk tabel `absensi_salma`
--
ALTER TABLE `absensi_salma`
  ADD PRIMARY KEY (`id_absensi_salma`),
  ADD KEY `id_user_salma` (`id_user_salma`);

--
-- Indeks untuk tabel `bonus_template_salma`
--
ALTER TABLE `bonus_template_salma`
  ADD PRIMARY KEY (`id_bonus_template`);

--
-- Indeks untuk tabel `gaji_salma`
--
ALTER TABLE `gaji_salma`
  ADD PRIMARY KEY (`id_gaji_salma`),
  ADD UNIQUE KEY `unique_gaji_per_bulan` (`id_user_salma`,`bulan_gaji_salma`,`tahun_gaji_salma`),
  ADD KEY `id_user_salma` (`id_user_salma`);

--
-- Indeks untuk tabel `hari_libur_salma`
--
ALTER TABLE `hari_libur_salma`
  ADD PRIMARY KEY (`id_libur_salma`),
  ADD UNIQUE KEY `tanggal_libur_salma` (`tanggal_libur_salma`);

--
-- Indeks untuk tabel `izin_salma`
--
ALTER TABLE `izin_salma`
  ADD PRIMARY KEY (`id_izin_salma`),
  ADD KEY `id_user_salma` (`id_user_salma`);

--
-- Indeks untuk tabel `jabatan_salma`
--
ALTER TABLE `jabatan_salma`
  ADD PRIMARY KEY (`id_jabatan_salma`);

--
-- Indeks untuk tabel `jam_absen_salma`
--
ALTER TABLE `jam_absen_salma`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `pengajuan_khusus_salma`
--
ALTER TABLE `pengajuan_khusus_salma`
  ADD PRIMARY KEY (`id_khusus`),
  ADD KEY `id_user_salma` (`id_user_salma`);

--
-- Indeks untuk tabel `potongan_template_salma`
--
ALTER TABLE `potongan_template_salma`
  ADD PRIMARY KEY (`id_potongan_template`);

--
-- Indeks untuk tabel `request_admin_salma`
--
ALTER TABLE `request_admin_salma`
  ADD PRIMARY KEY (`id_request`);

--
-- Indeks untuk tabel `response_admin_salma`
--
ALTER TABLE `response_admin_salma`
  ADD PRIMARY KEY (`id`),
  ADD KEY `request_id` (`request_id`);

--
-- Indeks untuk tabel `rfid_kartu_salma`
--
ALTER TABLE `rfid_kartu_salma`
  ADD PRIMARY KEY (`id_kartu`),
  ADD KEY `id_user_salma` (`id_user_salma`);

--
-- Indeks untuk tabel `slip_gaji_salma`
--
ALTER TABLE `slip_gaji_salma`
  ADD PRIMARY KEY (`id_slip_gaji_salma`),
  ADD UNIQUE KEY `nomor_slip_salma` (`nomor_slip_salma`),
  ADD KEY `id_gaji_salma` (`id_gaji_salma`);

--
-- Indeks untuk tabel `surat_peringatan_salma`
--
ALTER TABLE `surat_peringatan_salma`
  ADD PRIMARY KEY (`id_sp`),
  ADD KEY `id_user_salma` (`id_user_salma`);

--
-- Indeks untuk tabel `users_salma`
--
ALTER TABLE `users_salma`
  ADD PRIMARY KEY (`id_user_salma`),
  ADD UNIQUE KEY `username_salma` (`username_salma`),
  ADD UNIQUE KEY `email_salma` (`email_salma`),
  ADD UNIQUE KEY `nip_salma` (`nip_salma`),
  ADD KEY `fk_users_jabatan` (`id_jabatan_salma`);

--
-- AUTO_INCREMENT untuk tabel yang dibuang
--

--
-- AUTO_INCREMENT untuk tabel `absensi_salma`
--
ALTER TABLE `absensi_salma`
  MODIFY `id_absensi_salma` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=119;

--
-- AUTO_INCREMENT untuk tabel `bonus_template_salma`
--
ALTER TABLE `bonus_template_salma`
  MODIFY `id_bonus_template` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT untuk tabel `gaji_salma`
--
ALTER TABLE `gaji_salma`
  MODIFY `id_gaji_salma` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT untuk tabel `hari_libur_salma`
--
ALTER TABLE `hari_libur_salma`
  MODIFY `id_libur_salma` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;

--
-- AUTO_INCREMENT untuk tabel `izin_salma`
--
ALTER TABLE `izin_salma`
  MODIFY `id_izin_salma` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT untuk tabel `jabatan_salma`
--
ALTER TABLE `jabatan_salma`
  MODIFY `id_jabatan_salma` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT untuk tabel `jam_absen_salma`
--
ALTER TABLE `jam_absen_salma`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT untuk tabel `pengajuan_khusus_salma`
--
ALTER TABLE `pengajuan_khusus_salma`
  MODIFY `id_khusus` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT untuk tabel `potongan_template_salma`
--
ALTER TABLE `potongan_template_salma`
  MODIFY `id_potongan_template` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT untuk tabel `request_admin_salma`
--
ALTER TABLE `request_admin_salma`
  MODIFY `id_request` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT untuk tabel `response_admin_salma`
--
ALTER TABLE `response_admin_salma`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT untuk tabel `slip_gaji_salma`
--
ALTER TABLE `slip_gaji_salma`
  MODIFY `id_slip_gaji_salma` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT untuk tabel `surat_peringatan_salma`
--
ALTER TABLE `surat_peringatan_salma`
  MODIFY `id_sp` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- Ketidakleluasaan untuk tabel pelimpahan (Dumped Tables)
--

--
-- Ketidakleluasaan untuk tabel `pengajuan_khusus_salma`
--
ALTER TABLE `pengajuan_khusus_salma`
  ADD CONSTRAINT `pengajuan_khusus_salma_ibfk_1` FOREIGN KEY (`id_user_salma`) REFERENCES `users_salma` (`id_user_salma`) ON DELETE CASCADE;

--
-- Ketidakleluasaan untuk tabel `response_admin_salma`
--
ALTER TABLE `response_admin_salma`
  ADD CONSTRAINT `response_admin_salma_ibfk_1` FOREIGN KEY (`request_id`) REFERENCES `request_admin_salma` (`id_request`);

--
-- Ketidakleluasaan untuk tabel `rfid_kartu_salma`
--
ALTER TABLE `rfid_kartu_salma`
  ADD CONSTRAINT `rfid_kartu_salma_ibfk_1` FOREIGN KEY (`id_user_salma`) REFERENCES `users_salma` (`id_user_salma`) ON DELETE CASCADE;

--
-- Ketidakleluasaan untuk tabel `surat_peringatan_salma`
--
ALTER TABLE `surat_peringatan_salma`
  ADD CONSTRAINT `surat_peringatan_salma_ibfk_1` FOREIGN KEY (`id_user_salma`) REFERENCES `users_salma` (`id_user_salma`) ON DELETE CASCADE;

--
-- Ketidakleluasaan untuk tabel `users_salma`
--
ALTER TABLE `users_salma`
  ADD CONSTRAINT `fk_users_jabatan` FOREIGN KEY (`id_jabatan_salma`) REFERENCES `jabatan_salma` (`id_jabatan_salma`) ON DELETE SET NULL ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
