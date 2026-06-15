# Yayina Alma Notu

Bu proje Streamlit tabanli randevu sistemi. Kalici link icin en hizli yol Streamlit Community Cloud, daha saglam klinik kullanimi icin kalici veritabanli bir hosting gerekir.

## Hizli Kalici Link

Streamlit Community Cloud ile yapilir.

1. Proje GitHub'a yuklenir.
2. Streamlit Community Cloud'da `Create app` secilir.
3. Repository, branch ve `app.py` secilir.
4. Advanced settings icindeki `Secrets` alanina `.streamlit/secrets.example.toml` sablonundaki gercek degerler girilir.
5. Deploy edilir.

Bu yontem kalici bir URL verir. Streamlit Cloud dosya sistemi normalde kalici kabul edilmez. Bu projede `ENABLE_GOOGLE_DRIVE_BACKUP = true` acilirsa SQLite veritabani ve `uploads/` icindeki profil/logo/banner gorselleri Google Drive'a zip yedek olarak kaydedilir ve uygulama acilinca geri yuklenir.

## Daha Saglam Canli Kullanim

Kalici hasta randevulari icin Render, Railway, VPS veya benzeri bir ortamda kalici disk/veritabani kullanmak daha dogrudur.

Ortam degiskenleri:

```text
ADMIN_PASSWORD=guclu-sifre
DB_PATH=/kalici-disk/randevu_sistemi.db
UPLOAD_DIR=/kalici-disk/uploads
GOOGLE_CREDENTIALS_JSON={...}
GOOGLE_TOKEN_JSON={...}
ENABLE_GOOGLE_DRIVE_BACKUP=true
GOOGLE_DRIVE_BACKUP_NAME=hoca_randevu_kalici_yedek.zip
```

Start command:

```text
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

## GitHub'a Yuklenmemesi Gerekenler

- `.streamlit/secrets.toml`
- `credentials.json`
- `token.json`
- `randevu_sistemi.db`
- `uploads/`
- `*.log`
- `.venv/`

Bu dosyalar `.gitignore` icinde tutuluyor.

## Google Takvim ve Drive Yedegi

Canli yayinda Google izni tarayicida otomatik acilamaz. Bu nedenle token yerelde uretilir, sonra `GOOGLE_TOKEN_JSON` olarak canli ortama eklenir. Yeni Gmail'e gecilecekse token yeniden uretilip canli ortam secrets'i guncellenir.

Kalici veri yedegi icin token su iki izni birlikte icermelidir:

```text
https://www.googleapis.com/auth/calendar
https://www.googleapis.com/auth/drive.file
```

Google Cloud tarafinda Calendar API ve Drive API acik olmalidir.
