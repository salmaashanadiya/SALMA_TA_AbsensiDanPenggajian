import requests

FLASK_URL = "http://127.0.0.1:5000/rfid/absen"

def proses_scan(id_kartu):
    try:
        print(">>> KIRIM KE SERVER")

        r = requests.post(FLASK_URL, json={"id_kartu": id_kartu}, timeout=5)

        print("STATUS:", r.status_code)
        print("TEXT:", r.text)

        try:
            data = r.json()
        except:
            print("❌ Response bukan JSON\n")
            return

        status = data.get("status")

        if status == "MASUK":
            print(f"✅ MASUK - {data['nama']} ({data['jam']})")

        elif status == "PULANG":
            print(f"🔵 PULANG - {data['nama']} ({data['jam']})")

        elif status == "SUDAH_LENGKAP":
            print(f"⚠️ Sudah lengkap - {data['nama']}")

        elif status == "TIDAK_DIKENAL":
            print("❌ Kartu tidak dikenal")

        elif status == "NONAKTIF":
            print(f"🚫 Nonaktif - {data['nama']}")

        else:
            print("❓", data)

    except Exception as e:
        import traceback
        print("\n❌ ERROR:")
        traceback.print_exc()


while True:
    id_kartu = input("\nScan RFID: ").strip()
    if id_kartu:
        proses_scan(id_kartu)