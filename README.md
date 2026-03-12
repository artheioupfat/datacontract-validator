# boas_datacontract

Validation de la qualité d'un fichier `.parquet` via un [Data Contract](https://datacontract.com/) (YAML) et le CLI `datacontract-cli`.

---

## Structure du projet

```
boas_datacontract/
├── data/
│   └── export.parquet        # Fichier de données à valider
├── yaml
│   └── datacontract.yaml     # Contrat de données (schéma + qualité)
├── pyproject.toml
└── README.md
```

---

## Installation

### 1. Initialiser le projet et le venv

```bash
uv init boas_datacontract
cd boas_datacontract
uv venv --python 3.13
source .venv/bin/activate
uv python pin 3.13
```

> ⚠️ Vérifier dans `pyproject.toml` que `requires-python = ">=3.13"` et que `.python-version` contient `3.13`.

### 2. Ajouter les dépendances

```bash
uv add pyyaml
uv add 'datacontract-cli[parquet]'
uv add soda-core-duckdb
```


### Valider la syntaxe du contrat

```bash
datacontract lint yaml/datacontract.yaml
```

### Lancer les tests contre le fichier parquet

```bash
datacontract test --server local yaml/datacontract.yaml
```

### Résultat attendu

```
✅ data contract is valid
```

En cas d'erreur, le CLI affiche la colonne concernée et la valeur observée vs attendue :

```
🔴 data contract is invalid, found the following errors:
1) IPP Check that field IPP has no missing values: Value: 1
```

---

## Structure du datacontract.yaml

```yaml
dataContractSpecification: 0.9.3
id: urn:datacontract:export
info:
  title: Export Contract
  version: 1.0.0

servers:
  local:
    type: local
    path: ./data/export.parquet
    format: parquet

models:
  export:
    type: table
    fields:
      IPP:
        type: string
        required: true
      IEP:
        type: string
        required: true
      EVENT_TIME:
        type: timestamp
        required: true
      PRELEVEMENT_DATE:
        type: timestamp
        required: true
      UF:
        type: string
        required: true
      RESULTAT_TEXTE:
        type: string
        required: true

quality:
  type: SodaCL
  specification:
    checks for export:
      - not_null_percent(IPP) = 100
      - not_null_percent(IEP) = 100
      - not_null_percent(EVENT_TIME) = 100
      - not_null_percent(PRELEVEMENT_DATE) = 100
      - not_null_percent(UF) = 100
      - not_null_percent(RESULTAT_TEXTE) = 100
      - min(EVENT_TIME) >= '1925-01-01 00:00:00'
      - min(PRELEVEMENT_DATE) >= '1925-01-01 00:00:00'
```

---

## Modifier le contrat

### Ajouter une colonne

Dans `datacontract.yaml`, sous `models.export.fields` :

```yaml
MA_COLONNE:
  type: string
  required: true   # false si nullable autorisé
```

### Ajouter un test de qualité

Les tests se définissent dans le bloc `quality.specification`, en SodaCL.

#### Vérifier l'absence de valeurs nulles
```yaml
- not_null_percent(MA_COLONNE) = 100
```

#### Accepter un taux de nulls (ex: max 5%)
```yaml
- missing_percent(MA_COLONNE) < 5
```

#### Vérifier une valeur minimale
```yaml
- min(MA_COLONNE) >= 0
```

#### Vérifier une valeur maximale
```yaml
- max(MA_COLONNE) <= 120
```

#### Vérifier une date minimale
```yaml
- min(MA_DATE) >= '1925-01-01 00:00:00'
```

#### Vérifier l'unicité
```yaml
- duplicate_count(MA_COLONNE) = 0
```

#### Vérifier le nombre de lignes
```yaml
- row_count >= 1
```

Après chaque modification, relancer les tests :

```bash
datacontract test --server local datacontract.yaml
```

---

## Types de champs supportés

| Type YAML   | Type Parquet / DuckDB       |
|-------------|-----------------------------|
| `string`    | `VARCHAR`                   |
| `timestamp` | `TIMESTAMP WITH TIME ZONE`  |
| `integer`   | `INTEGER`                   |
| `number`    | `DOUBLE`                    |
| `boolean`   | `BOOLEAN`                   |