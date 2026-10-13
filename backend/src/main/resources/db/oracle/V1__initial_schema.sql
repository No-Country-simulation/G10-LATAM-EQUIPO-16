
    create table interaccion_cruda (
        created_at timestamp(9) not null,
        recibido_en timestamp(9),
        updated_at timestamp(9),
        id raw(16) not null,
        author varchar2(255 char),
        channel varchar2(255 char),
        fuente_comunidad varchar2(255 char),
        periodo_referencia varchar2(255 char),
        ruta_oci varchar2(255 char),
        status varchar2(255 char) not null check ((status in ('PENDING','PROCESSING','PROCESSED','ERROR','DISCARDED'))),
        type varchar2(255 char),
        text clob,
        primary key (id)
    );

    create table lote_distribucion (
        created_at timestamp(9) not null,
        updated_at timestamp(9),
        id raw(16) not null,
        fuente_comunidad varchar2(255 char) not null,
        oci_bucket varchar2(255 char),
        oci_namespace varchar2(255 char),
        periodo_referencia varchar2(255 char) not null,
        ruta_oci varchar2(255 char),
        status varchar2(255 char) not null check ((status in ('PENDING','PROCESSING','PROCESSED','ERROR'))),
        primary key (id)
    );
