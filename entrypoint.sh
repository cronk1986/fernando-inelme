#!/bin/bash

# ========================
# Configuración inicial
# ========================

# Variables configurables (pueden venir del entorno)
ODOO_VERSION="${ODOO_VERSION:-18.0}"
GIT_TOKEN="${GIT_TOKEN:-""}"
MODULES_DIR="/mnt/extra-addons"
DEFAULT_ADDONS="/mnt/custom-addons"
BACKUP_DIR="/odoo-backup"
CONFIG_FILE="/etc/odoo/odoo.conf"

# Definición de repos a clonar (se puede sobrescribir desde una variable de entorno)
CUSTOM_CLONE="
https://github.com/OCA/server-ux.git
https://github.com/OCA/web.git OCA/web
https://github.com/OCA/l10n-spain.git
https://github.com/OCA/reporting-engine.git
https://github.com/OCA/account-financial-tools.git
https://github.com/OCA/account-financial-reporting.git
https://github.com/OCA/account-invoicing.git
https://github.com/OCA/account-reconcile.git
https://github.com/OCA/helpdesk.git
https://github.com/OCA/timesheet.git
https://github.com/OCA/contract.git
https://github.com/OCA/project.git
https://github.com/OCA/mis-builder.git
https://github.com/OCA/crm.git
https://github.com/OCA/social.git
https://github.com/OCA/bank-payment.git
https://github.com/OCA/server-auth.git
https://github.com/OCA/community-data-files.git
https://github.com/OCA/bank-statement-import.git
https://github.com/OCA/spreadsheet.git
https://github.com/OCA/product-attribute.git
"

echo "[INFO] Iniciando entrypoint personalizado para Odoo $ODOO_VERSION"

# ========================
# Paso 1: Clonado de módulos y construcción de rutas
# ========================

mkdir -p "$MODULES_DIR"
mkdir -p "$DEFAULT_ADDONS"
ADDONS_PATH_SET=()  # Lista única para addons_path

if [[ -z "$CUSTOM_CLONE" ]]; then
  echo "[INFO] No hay repositorios definidos en CUSTOM_CLONE. Saltando clonado."
else
  echo "[INFO] Clonando módulos desde CUSTOM_CLONE (rama: $ODOO_VERSION)"

  while IFS= read -r line; do
    [[ -z "$line" || "$line" =~ ^[[:space:]]*$ ]] && continue

    REPO_URL=$(echo "$line" | awk '{print $1}')
    DEST_RELATIVE=$(echo "$line" | awk '{print $2}')

    # Si no se define destino explícito, lo inferimos de la URL
    if [[ -z "$DEST_RELATIVE" ]]; then
      DEST_RELATIVE=$(echo "$REPO_URL" | sed -E 's|https://[^/]+/||' | sed -E 's|\.git$||')
    fi

    DEST_DIR="$MODULES_DIR/$DEST_RELATIVE"

    # Añadir token si está definido
    if [[ -n "$GIT_TOKEN" ]]; then
      REPO_URL="https://${GIT_TOKEN}@${REPO_URL#https://}"
    fi

    # Clonar sólo si no existe
    if [[ -d "$DEST_DIR/.git" ]]; then
      echo "[INFO] Ya existe $DEST_DIR, omitiendo clonado."
    else
      echo "[INFO] Clonando $REPO_URL → $DEST_DIR"
      mkdir -p "$DEST_DIR"
      git clone --depth 1 --branch "$ODOO_VERSION" "$REPO_URL" "$DEST_DIR"
    fi

    # Asignar permisos adecuados
    chown -R odoo:odoo "$DEST_DIR"

    # Añadir a lista de addons_path si no está aún
    [[ ! " ${ADDONS_PATH_SET[@]} " =~ " $DEST_DIR " ]] && ADDONS_PATH_SET+=("$DEST_DIR")

  done <<< "$CUSTOM_CLONE"
fi

# ========================
# Paso 2: Preparar directorio de backups
# ========================

mkdir -p "$BACKUP_DIR"
chmod 777 "$BACKUP_DIR"
chown -R odoo:odoo "$BACKUP_DIR"

# ========================
# Paso 3: Construir addons_path final
# ========================

# Añadir rutas obligatorias (sin duplicados)
[[ ! " ${ADDONS_PATH_SET[@]} " =~ " $DEFAULT_ADDONS " ]] && ADDONS_PATH_SET+=("$DEFAULT_ADDONS")
[[ ! " ${ADDONS_PATH_SET[@]} " =~ " $MODULES_DIR " ]] && ADDONS_PATH_SET+=("$MODULES_DIR")

# Unir con comas
FINAL_ADDONS_PATH=$(IFS=, ; echo "${ADDONS_PATH_SET[*]}")

echo "[INFO] Usando addons_path: $FINAL_ADDONS_PATH"

# ========================
# Paso 4: Generar archivo de configuración
# ========================

cat > "$CONFIG_FILE" <<EOF
[options]
addons_path = $FINAL_ADDONS_PATH
admin_passwd = ${ADMIN_PASSWORD}
db_host = ${DB_HOST}
db_port = ${DB_PORT}
db_user = ${DB_USER}
db_password = ${DB_PASSWORD}
log_level = ${LOG_LEVEL}
data_dir = /var/lib/odoo
workers = ${ODOO_WORKERS:-1}
dbfilter = ${DB_FILTER}
xmlrpc_port = 8069
longpolling_port = 8072
;gevent_port = 8072
;limit_time_real_cron = 120
websocket_keep_alive_timeout = 600
websocket_rate_limit_burst = 10
websocket_rate_limit_delay = 0.2
proxy_mode = True
logfile = 
EOF

# ========================
# Paso 5: Ejecutar proceso principal
# ========================

exec "$@"
