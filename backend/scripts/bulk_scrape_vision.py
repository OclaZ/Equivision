import os
import time
import requests
import json
from pathlib import Path

# --- CONFIGURATION ---
BASE_DIR = Path("d:/EquiVision/backend/data/raw/horse-breeds/")
LABELS_PATH = BASE_DIR / "labels.json"

# Breed IDs to Names (Single Source of Truth)
BREED_MAP = {
    "01": "Akhal-Teke",
    "02": "Appaloosa",
    "03": "Orlov Trotter",
    "04": "Vladimir Heavy Draft",
    "05": "Percheron",
    "06": "Arabian",
    "07": "Friesian",
    "08": "Barb",
    "09": "Andalusian",
    "10": "Hanoverian",
    "11": "Lusitano"
}

# Image URLs from Wikimedia Commons (High Quality, Direct URLs)
IMAGE_DATA = {
  "08": [ # Barb
    "https://upload.wikimedia.org/wikipedia/commons/a/a9/A_Moroccan_horse_standing_before_an_arch_MET_DP876104.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/7/72/Arabian_Moroccan_Knight.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/8/8c/Barb_Horse_tbourida_Morocco.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/1/13/Barb_Horses_from_Moussem_Moulay_Abdallah_Amghar_14.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/a/a0/Barb_Horses_from_Moussem_Moulay_Abdallah_Amghar_15.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/1/1d/Barb_Horses_from_Moussem_Moulay_Abdallah_Amghar_16.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/1/13/Barb_Horses_from_Moussem_Moulay_Abdallah_Amghar_18.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/7/7c/Barb_Horses_from_Moussem_Moulay_Abdallah_Amghar.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/f/fb/Barbe_bai_fantasia.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/7/75/Barbe_de_la_r%C3%A9gion_d%27Alger.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/d/d7/Barbe_du_Gharb_%28Maroc_occidental%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/8/89/Barbe_du_Gharb_mont%C3%A9_par_un_couple.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/1/1c/Barbe_du_Gharb.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/5/59/Barbe_harnachement_officier.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/b/b4/Barbe_harnachement_spahi.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/d/d1/Barbe_Horse_01.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/6/67/Barbe_horse.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/1/1d/BARBE_MAROCAIN_1.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/a/a3/BARBE_MAROCAIN_2.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/7/7d/Barbe_profil_%282%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/6/6e/Barbe_tunisien_gris%2C_Tozeur.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/c/c7/Baron-d-Eisenberg-barbe.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/d/d3/Berber_horse.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/e/e5/Berber_warriors_show.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/b/ba/Beudant-Mimoun_trot_extension.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/d/d7/Cavaliers_berb%C3%A8res_attendant_la_fantasia_-_Mekn%C3%A8s_-_M%C3%A9diath%C3%A8que_de_l%27architecture_et_du_patrimoine_-_AP62T089306.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/6/6c/Cheval_barbe_-_Albert_Adam%2C_1903.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/7/73/Cheval_Barbe_-_Baron_de_Vaux.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/d/dc/Cheval_Barbe_-_Micado_de_face_dans_box_%28IMG_6601%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/c/c1/Cheval_barbe_a_bouchaoui.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/f/fc/Cheval_Barbe_colonial_de_1930.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/b/be/Cheval_barbe_et_petit_cavalier_de_Tanger.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/4/45/Cheval_Barbe_profil.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/9/93/Cheval_de_race_barbe.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/5/5f/Cheval_du_Rif%2C_1930_%282%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/8/80/Cheval_du_Rif%2C_1930.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/e/ed/Cheval_%C3%A0_El_Battan_02.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/6/6f/Cheval_%C3%A0_El_Battan_03.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/7/7b/Chevaux_de_Mogador_%282%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/8/87/Chevaux_de_Mogador.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/5/53/Chevaux_du_Gharb.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/e/ee/Falconiere_in_burnus.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/a/a1/Fantazia_My_Abdellah_3_cavl%C3%AEs.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/d/d5/Fils_de_ca%C3%AFd_sur_un_cheval_de_fantasia_-_Camp_Boulhaut_-_M%C3%A9diath%C3%A8que_de_l%27architecture_et_du_patrimoine_-_AP62T059311.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/4/43/Jeune_Barbe_attel%C3%A9_Tozeur.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/e/e1/Jpg_15805803013666506.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/b/b0/Jument_Barbe_Tunis.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/8/80/Jument_du_Rif.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/3/35/Karoubi%2C_Barbe_de_la_tribu_des_Ouled-Mimoun.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/1/18/Les_races_chevalines_%28Page_12%29_BHL22833025_%28cropped%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/4/46/Loyaut%C3%A9%2C_Barbe%2C_1930.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/2/28/Loyaut%C3%A9%2C_Barbe%2C_Vichy_1924.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/f/f8/Mchaf_%28cropped%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/7/75/Mchaf.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/a/a0/Medina%2C_Meknes%2C_Morocco_-_panoramio_%283%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/9/95/Messaoud_Barbe_saut_d%27attelage.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/a/a8/Moussem_moulay_abdellah_-_Moulay_Abdallah_Amghar_commune_19.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/9/9d/Spanish_Barb_Stallion.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/5/55/The_origin_and_influence_of_the_thoroughbred_horse_%28Page_384%29_BHL20011006.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/2/2e/Type_de_soldat_combattant_les_Espagnols_dans_le_Rif.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/d/d7/Un_cavalier_Marocain_%28cropped%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/8/84/Un_cavalier_Marocain.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/8/8f/Volontaire%2C_Barbe_n%C3%A9_en_1893.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/9/94/Wei%C3%9Fer_Berber_%28132669295%29.jpeg",
    "https://upload.wikimedia.org/wikipedia/commons/8/83/WELBECK_Paragon_un_Barbe.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/f/f0/Zafira_Al_Saida_0001.jpg"
  ],
  "09": [ # Andalusian
    "https://upload.wikimedia.org/wikipedia/commons/5/58/10.Moriles_Caballo.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/4/4b/Anthony_van_Dyck_-_An_Andalusian_horse.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/7/7f/2004._Stamp_of_Belarus_0581-0584.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/6/66/2010_Feria_Saintes_25.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/5/5e/Alborozo_10_%282690566112%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/b/b0/Alborozo_11_%282690566038%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/c/c7/Alborozo_12_%282689754253%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/5/54/Alborozo_13_%282690565878%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/e/e2/Alborozo_14_%282689754081%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/d/d3/Alborozo_15_%282690565734%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/e/e0/Andalusian_2.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/b/b5/Andalusian_backlook.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/5/56/Andalusian_horse_moscow.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/7/7a/Andalusian_horse.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/7/77/ANdalusian_Stallion_getting_a_bath_and_enjoying_the_water_on_a_hot_day_at_the_Kentucky_Horse_Park_%285966849386%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/4/4f/Andalusian-vitiligo.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/5/57/Andalusian.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/6/65/Andalusian1.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/b/bf/Andalusian2.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/3/3e/Andalusian3.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/0/0e/Andalusier_-_Kopf.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/1/15/Andalusier_-_r%C3%BCckw%C3%A4rtsgehend.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/5/54/Andalusier_-_Vorf%C3%BChrung_spanischer_Rassen3_best.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/6/66/Andalusier_-_Vorf%C3%BChrung_spanischer_Rassen6.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/2/2f/Andalusier_1_voll_versammelt.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/e/e8/Andalusier_3_-_galoppierend.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/b/bf/Andalusier_3_Gang_Halle_10.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/4/47/Andalusier_beim_Waelzen_82a.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/a/af/Andalusier_steigend.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/1/1b/Andalusier_vor_dem_Waelzen_81a.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/f/f3/Andalusierhengst_25a.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/d/d4/Andalusierhengst_93c.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/1/1f/Batidores_en_uniforme_de_instrucci%C3%B3n.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/6/68/Cabalo044eue.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/2/20/Campe%C3%B3n_de_Campeones_2016_P1020553.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/3/3f/Eggbutt.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/a/a6/Flamenco-Caballo-Dsc02992.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/2/20/Flamenco-Caballo-Dsc02994.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/0/0d/Flamenco-Caballo-Dsc02995.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/5/54/Flamenco-Caballo-Dsc02996.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/c/cf/Flamenco-Caballo-Dsc02998.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/7/75/Flamenco-Caballo-Dsc03000.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/4/4d/Flamenco-Caballo-Dsc03003.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/8/87/Flamenco-Caballo-Dsc03011.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/3/3f/Flamenco-Caballo-Dsc03012.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/4/44/Flehmendes_Pferd_32_c.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/b/b6/Jacob_de_Gheyn_%28II%29_Spanish_battle_stallion_1603.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/e/e6/Head_study_of_the_Pearl_stallion%2C_Majodero_R..JPG",
    "https://upload.wikimedia.org/wikipedia/commons/4/43/I_believe_that_this_is_the_Andalusian_Stallion_Pecos_%285966346891%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/e/e7/IMAN_-_Eduardo_Vargas..jpg",
    "https://upload.wikimedia.org/wikipedia/commons/0/03/Jaume_I_al_Puig.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/5/5c/Jerez-Flamenco-Caballo-dsc02995.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/c/c8/Jinetes.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/c/ca/Kraft_001_Img1769_%28185770059%29.jpeg",
    "https://upload.wikimedia.org/wikipedia/commons/f/fb/Kraft_003_Img_1977_2_Jpg_%28185770117%29.jpeg",
    "https://upload.wikimedia.org/wikipedia/commons/d/d9/Kraft_008_Img2058_%28185770145%29.jpeg",
    "https://upload.wikimedia.org/wikipedia/commons/7/74/Kraft_009_Img_2256_2_Jpg_%28185770165%29.jpeg",
    "https://upload.wikimedia.org/wikipedia/commons/1/1c/Kraft_010_Img2293_%28185770151%29.jpeg",
    "https://upload.wikimedia.org/wikipedia/commons/a/a4/Listo_on_set.jpeg",
    "https://upload.wikimedia.org/wikipedia/commons/f/f9/Pferd_82f.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/9/9a/PfingstTunier_2013_Kutschen-Korso_Reiter_spanisch_b.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/4/45/PfingstTunier_2013_Kutschen-Korso_Reiter_spanisch.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/3/31/The_Andalusian_X_Lusitano_cross_is_known_on_the_Iberian_Peninsula_as_the_%22Golden_Cross%22_._._..JPG",
    "https://upload.wikimedia.org/wikipedia/commons/2/23/Uraneo_Bay_Andalusian_%28Half_brother_to_Alborozo%29_%282690237479%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/9/99/Vaq7.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/e/ed/%C3%81lvaro_Montes.JPG"
  ],
  "10": [ # Hanoverian
    "https://upload.wikimedia.org/wikipedia/commons/7/72/%28Noch_ein%29_freches_M%C3%A4dchen.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/b/bf/2018FEI-WORLD-CUP-DRESSAGE-Belinda-Weinbauer.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/9/95/2018FEI-WORLD-CUP-DRESSAGE-Hayley-Watson-Greaves.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/e/e7/2018FEI-WORLD-CUP-DRESSAGE-Shelly-Francis.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/b/bd/2022-10-23_B%C3%BCrgermeister-K%C3%B6hler-Stra%C3%9Fe_8_in_H%C3%B6ver.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/e/e1/2022-10-23_B%C3%BCrgermeister-K%C3%B6hler-Stra%C3%9Fe_8%2C_H%C3%B6ver.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/c/c7/Andreas_Dibowski_%28GER%29_2013.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/c/c8/Andreas_dibowski_frh_fantasia_quarry_badminton_2011.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/0/04/Andreas_Dibowski_Leon_-_DM_Schenefeld_2013.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/4/4a/Andreas_Dibowski_mit_Avedon%2C_CIC_3_Luhm%C3%BChlen.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/d/df/Andreas_Dibowski_mit_FRH_Fantasia_-_CIC_3-W_Schenefeld.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/0/02/Andreas_Dibowski_mit_Leon%2C_CCI_4_Luhm%C3%BChlen.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/e/ee/Beijing2008_eq_medal_Dressage_Team_03.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/1/1b/Beijing2008_HOKETSU_Hiroshi.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/0/09/Cadre_noir_-_Jean-Paul_Largy_et_Sans_Pareil.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/a/a7/Cadre_noir_-_Laurence_Sautet_et_Sontero.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/9/93/Cadre_noir_-_Nadege_Bourdon_et_Rapsodie.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/c/c4/Cadre_noir_-_Nad%C3%A8ge_Bourdon_et_Rapsodie_11.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/e/e7/Carde_noir_-_Pauline_Basquin_et_Liaison.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/2/22/Eerelman-hannover.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/d/d6/Elisabeth_Theurer_%28AUT%29_1980.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/1/14/ENE_Sontero_HAN.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/7/72/Gesthunnoh.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/2/2e/Hannoveraner_auf_Schwanheimer_D%C3%BCne_1.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/4/41/Hannoveraner_Dressur_Goethe_3_bestes.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/5/57/Hannoveraner_Dressur_Romantic_Boy1.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/b/b9/Hannoveraner_Dressur_Romantic_Boy2.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/c/ce/Hanoverian-hunter.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/1/13/Haras_du_Pin_Belfort_HAN.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/9/9f/HengstWohlklang.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/a/a2/Hunnesrueck_stud_stallions_hay_feeding.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/5/58/Ingrid_Klimke_Butts_Abraxxas_cross_country_London_2012.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/5/59/Ingrid_Klimke_FRH_Butts_Abraxxas_Badminton_2011.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/6/68/Ingrid_klimke_frh_butts_abraxxas_shogun_hollow_badminton_2011.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/f/fb/Ingrid_Klimke_und_Butts_Abraxxas_-_CIC_Schenefeld_2010.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/c/c0/Ingrid_Klimke_und_Butts_Abraxxas%2C_Dressur%2C_EM_Vielseitigkeit_2011.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/e/e4/Ingrid_Klimke_und_Butts_Abraxxas%2C_Hindernis_16c%2C_CIC_Schenefeld_2010.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/7/73/Isabell_Werth_Beijing_2008.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/e/eb/Lisa_Wilcox_-_Pikko_del_Cerro_-_CDI_Wellington_2013.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/7/7a/Marcus_Ehning_mit_For_Germany1.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/2/2f/Mon_Cherie_2_1980-1-.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/7/74/Mon_Cherie_2_1980-1-s.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/a/a3/Niedersachsenhalle_Totale.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/e/e5/RCMP_Farm_Hannoverian.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/8/81/RCMP_Farm_Hannoverian1.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/c/cc/RCMP_Farm_Hannoverian2.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/9/93/Simone_Blum_%28GER%29_2011.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/d/d4/Springreiten_Simone_Blum_auf_Pferd_Flying_Boy_International_2011.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/d/d6/Sunny_horse.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/c/c9/Uno_%28hannoveraner%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/d/d8/WC07d.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/0/0b/WPT2013-CDI4-Frahm_Steffen-Damsey-2.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/c/c9/WPT2013-CDI4-Frahm_Steffen-Damsey-3.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/b/b7/WPT2013-CDI4-Frahm_Steffen-Damsey-4.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/9/90/WPT2013-CDI4-Frahm_Steffen-Damsey-5.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/9/91/WPT2013-CDI4-Principe_Luis-World_Performance_Washington-2.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/f/f5/WPT2013-CDI4-Principe_Luis-World_Performance_Washington-4.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/1/14/WPT2013-CDI4-Principe_Luis-World_Performance_Washington-5.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/d/d0/WPT2013-CIC3-D-Andreas_Dibowski-FRH_Fantasia-1.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/c/c1/WPT2013-CIC3-D-Andreas_Dibowski-FRH_Fantasia-2.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/2/28/WPT2013-CIC3-D-Andreas_Dibowski-FRH_Fantasia-3.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/4/44/WPT2013-CIC3-D-Andreas_Dibowski-FRH_Fantasia-4.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/e/ea/WPT2013-CIC3-D-Josefa_Sommer-Hamilton-1.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/0/0c/WPT2013-CIC3-D-Josefa_Sommer-Hamilton-2.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/9/91/WPT2013-CIC3-D-Josefa_Sommer-Hamilton-3a.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/7/7f/WPT2013-CIC3-D-Josefa_Sommer-Hamilton-3b.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/e/ef/WPT2013-CIC3-Dibowski_Andreas-FRH_Fantasia-1.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/0/0c/WPT2013-CIC3-Klimke_Ingrid-FRH_Escada_JS-1.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/3/3b/WPT2013-CIC3-Klimke_Ingrid-FRH_Escada_JS-2.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/1/14/WPT2013-CIC3-Klimke_Ingrid-FRH_Escada_JS-3.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/e/ed/WPT2013-CIC3-S-Andreas_Dibowski-FRH_Fantasia-1.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/9/96/WPT2013-CIC3-S-Andreas_Dibowski-FRH_Fantasia-2.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/2/22/WPT2013-CIC3-S-Ingrid_Klimke-FRH_Escada_JS-1.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/2/2f/WPT2013-CIC3-S-Ingrid_Klimke-FRH_Escada_JS-2.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/1/1d/WPT2013-CIC3-S-Ingrid_Klimke-FRH_Escada_JS-3.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/3/35/WPT2013-CIC3-S-Josefa_Sommer-Hamilton-1.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/6/67/WPT2013-CIC3-Sommer_Josefa-Hamilton-1.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/3/39/WPT2013-CIC3-Sommer_Josefa-Hamilton-2.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/a/a7/WPT2013-CSIYH1-K%C3%BChner%2CMax-Giselle-3.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/6/65/WPT2013-CVI-Johanna_Schumann-Martina_K%C3%B6hler-Freaky_Frank-2.JPG"
  ],
  "11": [ # Lusitano
    "https://upload.wikimedia.org/wikipedia/commons/1/12/Ant%C3%B3nio_Telles_numa_lide_a_cavalo_na_Ilha_Terceira.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/4/4a/Awaiting_a_bull_strike_in_Campo_Pequeno.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/0/00/Beja_lusitano.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/4/4d/Carlos_Pereira_et_Distinto.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/2/25/Carlos_Pereira_sur_Bemposto_et_Distinto_au_piaffer.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/0/02/Carlos_Pinto_et_Notavel_Olympic_Games_Pekin_2008.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/d/dd/Carlos_Pinto_et_Soberano_%C3%A0_Saumur.png",
    "https://upload.wikimedia.org/wikipedia/commons/5/5e/Carlos_Pinto%2C_cavalier_dresseur_international_dressage.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/b/b2/Carlos_Pinto%2C_cavalier_olympic_de_dressage_et_entraineur_international.png",
    "https://upload.wikimedia.org/wikipedia/commons/3/38/Catherine_Henriquet_and_Orph%C3%A9e_in_Versailles.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/3/39/Cavaleiro_taurom%C3%A1quico_%28Ch.-Fl._111-6565%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/f/f1/Cavalerie_portugaise.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/6/67/Cheval_lusitanien.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/a/a2/Cheval_lusitanien1.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/0/09/Cheval_Passion_2022_-_Man%C3%A8ge_exterieur_33.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/7/7e/Classic_dressage%2C_Carlos_Pereira_and_Distinto.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/5/50/DIAMANTE_-_POTRO_LUSITANO_-_YEGUADA_LA_PERLA.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/2/28/Diego_Ventura_en_Arles_-_Feria_du_Riz_2009.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/8/89/Dressage_stallion_3.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/4/47/Eguada_%28207878585%29.jpeg",
    "https://upload.wikimedia.org/wikipedia/commons/6/68/Equitation_portugaise.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/d/d9/Estrela_Mar%C3%A7o_2010-40.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/7/71/Feira_Nacional_do_Cavalo_67a.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/2/28/FranceNormandieCaenJEM2014DOrnanoJoaoVictorOlivaSignoDosPinhais.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/4/4e/Grey_lusitano.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/b/b8/Hipismo_adestramento_1_15072007.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/a/ad/Horse_December_2014-3.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/7/75/Horse_time_trials_-_Fatacil_Agriculture_and_Tourism_Fair_-_Lagoa_-_The_Algarve%2C_Portugal_%281470299922%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/d/d1/Jos%C3%A9_Pedro_Bil%C3%A9u.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/c/ce/Juments_lusitaniennes_01.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/c/c0/Juments_lusitaniennes_02.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/6/64/Juments_lusitaniennes_04.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/0/05/Juments_lusitaniennes_05.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/d/d1/Juments_lusitaniennes_06.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/3/30/Juments_lusitaniennes_07.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/c/c6/Juments_lusitaniennes_08.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/1/10/Juments_lusitaniennes_12.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/9/9b/Juments_lusitaniennes_16.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/8/8c/Juments_lusitaniennes_17.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/5/5d/Juments_lusitaniennes_18.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/c/cc/Lea_Vicens_en_la_plaza_de_toros_de_M%C3%A1laga.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/7/76/Lea_Vicens.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/e/e0/Lusitano_cremello.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/1/16/Lusitano_Hengst_%28132668445%29.jpeg",
    "https://upload.wikimedia.org/wikipedia/commons/5/54/Lusitano_Pferd_International_2011.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/2/22/Lusitano_Pride_%28236350537%29.jpeg",
    "https://upload.wikimedia.org/wikipedia/commons/f/f9/Lusitano_stallion1.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/8/8c/Lusitano_violino.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/c/c4/Lusitano.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/0/06/L%C3%A9a_Vicens.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/d/db/Natural_Lusitano_Instinct_%28236483203%29.jpeg",
    "https://upload.wikimedia.org/wikipedia/commons/6/64/Pablo_Hermoso_de_Mendoza_2.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/5/5a/Palefrenier_et_jument_Lusitanienne.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/5/51/Piqueurs_en_parade_%28Portugal%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/5/59/Rejoneador_Guillermo_P%C3%A9rez_Cardoso.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/f/fa/Rejoneo_01.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/1/1e/Rogerio_da_Silva_Clementino-WEG_2010_01.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/a/ae/Roi_Manuel_du_Portugal_a_cheval_%28h%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/a/ac/Roi_Manuel_du_Portugal_a_cheval_%28v%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/8/8a/ROMA_443.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/8/80/Scene_de_rue_a_Lisbonne_-_cavalier.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/b/bd/Soberano_III_et_Carlos_Pinto_JEM_2014.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/e/e5/Soin_ant%C3%A9rieur_droit_sur_jument.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/4/46/Soins_ant%C3%A9rieur_droit_sur_jument2.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/3/31/The_Andalusian_X_Lusitano_cross_is_known_on_the_Iberian_Peninsula_as_the_%22Golden_Cross%22_._._..JPG",
    "https://upload.wikimedia.org/wikipedia/commons/9/92/Toureiro_prestes_a_espetar_umas_bandarilhas_num_Touro_no_Campo_Pequeno.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/7/7e/URBAN_LEGEND_EQUI_REV_%C3%A9talon_race_creme.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/2/24/Veterinary_cares_on_7_years_mare_-_2.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/d/dd/Veterinary_cares_on_7-years-old-mare.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/4/4e/WEG_2010_-_Dressage_Qualifying.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/7/7b/WPT2013-CDI4-Carvalho_Goncalo-Rubi-2.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/c/c4/WPT2013-CDI4-Carvalho_Goncalo-Rubi-3.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/0/0b/WPT2013-CDI4-Carvalho_Goncalo-Rubi-5.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/9/9f/WPT2013-CDI4-Palma_Santos_Nuno-Sal-2.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/2/20/WPT2013-CDI4-Palma_Santos_Nuno-Sal-3.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/0/0a/WPT2013-CDI4-Palma_Santos_Nuno-Sal-4.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/6/6b/WPT2013-CDI4-Palma_Santos_Nuno-Sal-5.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/2/27/WPT2013-CDI4-Palma_Santos_Nuno-Sal-6.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/7/73/YEGUADA_LA_PERLA.JPG"
  ]
}

def download_image(url, target_path):
    # More descriptive User-Agent as per Wikimedia policy
    headers = {
        'User-Agent': 'EquiVisionBot/1.0 (Educational Research Project; +mailto:admin@equivision.com) python-requests/2.31'
    }
    retries = 3
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                with open(target_path, 'wb') as f:
                    f.write(response.content)
                return True
            elif response.status_code == 429:
                wait_time = (attempt + 1) * 2
                print(f"  429 Too Many Requests. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                print(f"  Error {response.status_code} for {url}")
                # Don't retry on 404
                if response.status_code == 404:
                    return False
                time.sleep(1)
                continue
        except Exception as e:
            print(f"  Exception for {url} (Attempt {attempt+1}/{retries}): {e}")
            time.sleep(2)
            continue
    return False

def main():
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save unified labels.json
    with open(LABELS_PATH, 'w') as f:
        json.dump(BREED_MAP, f, indent=4)
    print(f"Unified labels.json saved with {len(BREED_MAP)} classes.")

    for breed_id, urls in IMAGE_DATA.items():
        breed_name = BREED_MAP[breed_id]
        print(f"\nProcessing {breed_name} ({breed_id})...")
        downloaded = 0
        for i, url in enumerate(urls):
            # Check file extension from URL
            ext = 'jpg'
            if 'png' in url.lower(): ext = 'png'
            elif 'jpeg' in url.lower(): ext = 'jpg'
            elif 'webp' in url.lower(): ext = 'webp'
            
            file_name = f"{breed_id}_{i+1:03}.{ext}"
            target_path = BASE_DIR / file_name
            
            if target_path.exists():
                # Check if file is valid/non-empty
                if target_path.stat().st_size > 0:
                    print(f"  Existing: {file_name}")
                    downloaded += 1
                    continue
                else:
                    print(f"  Removing empty file: {file_name}")
                    os.remove(target_path)

            if download_image(url, target_path):
                print(f"  Downloaded: {file_name}")
                downloaded += 1
                # Respectful delay - kept at 1.5s
                time.sleep(1.5)
            else:
                print(f"  Failed: {url}")
        
        print(f"Total {breed_name}: {downloaded}/{len(urls)}")

if __name__ == "__main__":
    main()
