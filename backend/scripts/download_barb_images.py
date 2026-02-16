import os
import urllib.request
from pathlib import Path

# Config
TARGET_DIR = Path("d:/EquiVision/backend/data/raw/horse-breeds/")
BREED_ID = "08"  # Barb
IMAGE_URLS = [
    "https://upload.wikimedia.org/wikipedia/commons/a/a9/A_Moroccan_horse_standing_before_an_arch_MET_DP876104.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/7/72/Arabian_Moroccan_Knight.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/8/8c/Barb_Horse_tbourida_Morocco.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/1/13/Barb_Horses_from_Moussem_Moulay_Abdallah_Amghar_14.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/a/a0/Barb_Horses_from_Moussem_Moulay_Abdallah_Amghar_15.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/1/1d/Barb_Horses_from_Moussem_Moulay_Abdallah_Amghar_16.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/1/13/Barb_Horses_from_Moussem_Moulay_Abdallah_Amghar_18.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/7/7c/Barb_Horses_from_Moussem_Moulay_Abdallah_Amghar.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/f/fb/Barbe_bai_fantasia.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/7/7d/Barbe_profil_%282%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/6/6e/Barbe_tunisien_gris%2C_Tozeur.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/e/e5/Berber_warriors_show.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/d/dc/Cheval_Barbe_-_Micado_de_face_dans_box_%28IMG_6601%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/c/c1/Cheval_barbe_a_bouchaoui.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/b/be/Cheval_barbe_et_petit_cavalier_de_Tanger.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/4/45/Cheval_Barbe_profil.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/9/93/Cheval_de_race_barbe.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/a/a1/Fantazia_My_Abdellah_3_cavl%C3%AEs.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/4/43/Jeune_Barbe_attel%C3%A9_Tozeur.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/e/e1/Jpg_15805803013666506.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/b/b0/Jument_Barbe_Tunis.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/f/f8/Mchaf_%28cropped%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/7/75/Mchaf.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/a/a0/Medina%2C_Meknes%2C_Morocco_-_panoramio_%283%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/a/a8/Moussem_moulay_abdellah_-_Moulay_Abdallah_Amghar_commune_19.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/9/9d/Spanish_Barb_Stallion.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/d/d7/Un_cavalier_Marocain_%28cropped%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/8/84/Un_cavalier_Marocain.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/9/94/Wei%C3%9Fer_Berber_%28132669295%29.jpeg",
    "https://upload.wikimedia.org/wikipedia/commons/f/f0/Zafira_Al_Saida_0001.jpg"
]

def download_images():
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    for i, url in enumerate(IMAGE_URLS):
        ext = url.split('.')[-1].lower()
        if ext not in ['jpg', 'jpeg', 'png', 'webp']:
            ext = 'jpg'  # fallback
            
        file_name = f"{BREED_ID}_{i+1:03}.{ext}"
        target_path = TARGET_DIR / file_name
        
        try:
            print(f"Downloading {url} to {target_path}...")
            # Use a User-Agent to avoid being blocked
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response, open(target_path, 'wb') as out_file:
                out_file.write(response.read())
            count += 1
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            
    print(f"Total images downloaded for breed {BREED_ID}: {count}")

if __name__ == "__main__":
    download_images()
