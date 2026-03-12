# datacontract-validator

Validation de la qualité d'un fichier `.parquet` via un [Data Contract](https://datacontract.com/) (YAML) et le CLI `datacontract-cli`.

---

## Structure du projet
```
boas_datacontract/
├── data/
│   └── export.parquet
├── yaml/
│   └── datacontract.yaml
├── pyproject.toml
└── README.md
```

---

## Dépendances
```bash
uv add pyyaml
uv add 'datacontract-cli[parquet]'
uv add soda-core-duckdb
```

---

## Commandes
```bash
# Valider la syntaxe du contrat
datacontract lint yaml/datacontract.yaml

# Lancer les tests contre le fichier parquet
datacontract test --server local yaml/datacontract.yaml
```

---

## datacontract.yaml

Le contrat suit le format défini par [datacontract-cli](https://cli.datacontract.com).