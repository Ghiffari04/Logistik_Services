# Sistem Logistik - Manajemen Ruangan

Sistem mikroservis untuk manajemen ruangan dan fasilitas kampus yang terdiri dari 5 layanan independen.

## Layanan

1. **RoomAvailabilityService (Port 5001)**
   - Cek jadwal ketersediaan ruangan/fasilitas kampus
   - Endpoint:
     - GET `/rooms` - Daftar semua ruangan
     - GET `/check-availability` - Cek ketersediaan ruangan

2. **RoomRecommendationService (Port 5002)**
   - Rekomendasikan ruangan yang cocok berdasarkan kebutuhan acara
   - Endpoint:
     - GET `/recommend-rooms` - Dapatkan rekomendasi ruangan

3. **RoomBookingService (Port 5003)**
   - Proses booking ruangan berdasarkan data acara
   - Endpoint:
     - POST `/book-room` - Buat booking ruangan baru
     - GET `/bookings/<event_id>` - Cek status booking

4. **BookingConfirmationService (Port 5004)**
   - Kirim status konfirmasi booking ruangan
   - Endpoint:
     - POST `/confirm-booking` - Konfirmasi booking
     - GET `/approval-status/<event_id>` - Cek status persetujuan

5. **RoomScheduleManagementService (Port 5005)**
   - Kelola dan update jadwal ruangan
   - Endpoint:
     - POST `/add-schedule` - Tambah jadwal baru
     - GET `/schedules/<room_id>` - Lihat jadwal ruangan
     - PUT `/update-schedule/<schedule_id>` - Update jadwal

## Teknologi

- Python 3.10
- Flask
- SQLAlchemy
- SQLite
- Docker
- Docker Compose

## Cara Menjalankan

1. Pastikan Docker dan Docker Compose terinstall di sistem
2. Clone repository ini
3. Buka terminal di direktori proyek
4. Jalankan perintah:
   ```bash
   docker-compose up --build
   ```
5. Layanan akan berjalan di port berikut:
   - RoomAvailabilityService: http://localhost:5001
   - RoomRecommendationService: http://localhost:5002
   - RoomBookingService: http://localhost:5003
   - BookingConfirmationService: http://localhost:5004
   - RoomScheduleManagementService: http://localhost:5005

## Struktur Data

### Room
- room_id (Integer, Primary Key)
- nama_ruangan (String)
- kapasitas (Integer)
- fasilitas (String)
- lokasi (String)

### RoomSchedule
- schedule_id (Integer, Primary Key)
- room_id (Integer, Foreign Key)
- tanggal_mulai (DateTime)
- tanggal_selesai (DateTime)
- status (String)
- event_id (Integer)

### Booking
- booking_id (Integer, Primary Key)
- event_id (Integer)
- room_id (Integer)
- tanggal_booking (DateTime)
- status_booking (String)

### EventApprovalLog
- approval_id (Integer, Primary Key)
- event_id (Integer)
- tanggal_approval (DateTime)
- status (String)
- catatan (String)

## Contoh Penggunaan API

### 1. Cek Ketersediaan Ruangan
```bash
curl "http://localhost:5001/check-availability?room_id=1&start_date=2024-03-20%2009:00:00&end_date=2024-03-20%2012:00:00"
```

### 2. Dapatkan Rekomendasi Ruangan
```bash
curl "http://localhost:5002/recommend-rooms?kapasitas=50&tanggal_mulai=2024-03-20%2009:00:00&tanggal_selesai=2024-03-20%2012:00:00&fasilitas=Proyektor"
```

### 3. Booking Ruangan
```bash
curl -X POST http://localhost:5003/book-room \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "room_id": 1,
    "tanggal_mulai": "2024-03-20 09:00:00",
    "tanggal_selesai": "2024-03-20 12:00:00"
  }'
```

### 4. Konfirmasi Booking
```bash
curl -X POST http://localhost:5004/confirm-booking \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "status": "APPROVED",
    "catatan": "Booking disetujui"
  }'
```

### 5. Lihat Jadwal Ruangan
```bash
curl "http://localhost:5005/schedules/1?start_date=2024-03-20%2000:00:00&end_date=2024-03-20%2023:59:59"
``` 