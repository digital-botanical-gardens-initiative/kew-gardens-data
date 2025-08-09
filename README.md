# Kew Botanical Gardens data

A minimal python script to merge .xlsx files from the Kew Botanical Gardens species list into a single CSV file.

## Data Source

The data in present in the `data/input` directory, which contains multiple `.xlsx` files. Each file corresponds to a different section of the species list.

## Script usage

```
python src/merger.py
```

The output data can be downloaded from the `data/output` directory as a single CSV file named `kew_species_list.csv`.

From the cli you can:

```
wget https://raw.githubusercontent.com/digital-botanical-gardens-initiative/kew-gardens-data/refs/heads/main/data/output/kew-species-list.csv
```
