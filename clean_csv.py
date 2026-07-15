import pandas as pd

DUPLICATES_PATH = "data/doublons_detectes.csv"

def run_clean_data_duplicated(original_df):
    df = original_df.copy()
    nb_doublons = df.duplicated().sum()

    if nb_doublons > 0:
        print(f"{nb_doublons} doublons détectés -> suppression en cours")

        # Sauvegarde de toutes les occurrences dupliquées avant suppression
        doublons = df[df.duplicated()]
        doublons.to_csv(DUPLICATES_PATH, index=False)
        print(f"[INFO] Doublons supprimés ont été historisés dans '{DUPLICATES_PATH}'.")

        # Suppression des doublons
        df = df.drop_duplicates()

    return df
