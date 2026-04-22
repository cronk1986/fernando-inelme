FROM odoo:18.0

USER root

RUN apt-get update && apt-get install -y python3-venv git && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
    dropbox \
    boto3 \
    pyncclient \ 
    nextcloud-api-wrapper \
    paramiko \
    psycopg2-binary \
    openupgradelib \
    schwifty==2024.4.0 \
    pycountry \
    packaging

RUN mkdir -p /mnt/custom-addons
RUN mkdir -p /odoo-backup

COPY ./custom-addons /mnt/custom-addons
RUN chown -R odoo:odoo /mnt/custom-addons /odoo-backup

COPY entrypoint.sh /entrypoint.sh

RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

# restore odoo user
USER odoo

ENTRYPOINT ["/entrypoint.sh"]
CMD ["odoo"]
