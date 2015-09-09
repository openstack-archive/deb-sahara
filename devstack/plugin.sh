#!/bin/bash
#
# lib/sahara

# Dependencies:
# ``functions`` file
# ``DEST``, ``DATA_DIR``, ``STACK_USER`` must be defined

# ``stack.sh`` calls the entry points in this order:
#
# install_sahara
# install_python_saharaclient
# configure_sahara
# start_sahara
# stop_sahara
# cleanup_sahara

# Save trace setting
XTRACE=$(set +o | grep xtrace)
set +o xtrace


# Functions
# ---------

# create_sahara_accounts() - Set up common required sahara accounts
#
# Tenant      User       Roles
# ------------------------------
# service     sahara    admin
function create_sahara_accounts {

    create_service_user "sahara"

    if [[ "$KEYSTONE_CATALOG_BACKEND" = 'sql' ]]; then

        # TODO: remove "data_processing" service when #1356053 will be fixed
        local sahara_service_old=$(openstack service create \
            "data_processing" \
            --name "sahara" \
            --description "Sahara Data Processing" \
            -f value -c id
        )
        local sahara_service_new=$(openstack service create \
            "data-processing" \
            --name "sahara" \
            --description "Sahara Data Processing" \
            -f value -c id
        )
        get_or_create_endpoint $sahara_service_old \
            "$REGION_NAME" \
            "$SAHARA_SERVICE_PROTOCOL://$SAHARA_SERVICE_HOST:$SAHARA_SERVICE_PORT/v1.1/\$(tenant_id)s" \
            "$SAHARA_SERVICE_PROTOCOL://$SAHARA_SERVICE_HOST:$SAHARA_SERVICE_PORT/v1.1/\$(tenant_id)s" \
            "$SAHARA_SERVICE_PROTOCOL://$SAHARA_SERVICE_HOST:$SAHARA_SERVICE_PORT/v1.1/\$(tenant_id)s"
        get_or_create_endpoint $sahara_service_new \
            "$REGION_NAME" \
            "$SAHARA_SERVICE_PROTOCOL://$SAHARA_SERVICE_HOST:$SAHARA_SERVICE_PORT/v1.1/\$(tenant_id)s" \
            "$SAHARA_SERVICE_PROTOCOL://$SAHARA_SERVICE_HOST:$SAHARA_SERVICE_PORT/v1.1/\$(tenant_id)s" \
            "$SAHARA_SERVICE_PROTOCOL://$SAHARA_SERVICE_HOST:$SAHARA_SERVICE_PORT/v1.1/\$(tenant_id)s"
    fi
}

# cleanup_sahara() - Remove residual data files, anything left over from
# previous runs that would need to clean up.
function cleanup_sahara {

    # Cleanup auth cache dir
    sudo rm -rf $SAHARA_AUTH_CACHE_DIR
}

# configure_sahara() - Set config files, create data dirs, etc
function configure_sahara {
    sudo install -d -o $STACK_USER $SAHARA_CONF_DIR

    if [[ -f $SAHARA_DIR/etc/sahara/policy.json ]]; then
        cp -p $SAHARA_DIR/etc/sahara/policy.json $SAHARA_CONF_DIR
    fi

    # Create auth cache dir
    sudo install -d -o $STACK_USER -m 700 $SAHARA_AUTH_CACHE_DIR
    rm -rf $SAHARA_AUTH_CACHE_DIR/*

    configure_auth_token_middleware $SAHARA_CONF_FILE sahara $SAHARA_AUTH_CACHE_DIR

    # Set admin user parameters needed for trusts creation
    iniset $SAHARA_CONF_FILE keystone_authtoken admin_tenant_name $SERVICE_TENANT_NAME
    iniset $SAHARA_CONF_FILE keystone_authtoken admin_user sahara
    iniset $SAHARA_CONF_FILE keystone_authtoken admin_password $SERVICE_PASSWORD

    iniset_rpc_backend sahara $SAHARA_CONF_FILE DEFAULT

    # Set configuration to send notifications

    if is_service_enabled ceilometer; then
        iniset $SAHARA_CONF_FILE DEFAULT enable_notifications "true"
        iniset $SAHARA_CONF_FILE DEFAULT notification_driver "messaging"
    fi

    iniset $SAHARA_CONF_FILE DEFAULT verbose True
    iniset $SAHARA_CONF_FILE DEFAULT debug $ENABLE_DEBUG_LOG_LEVEL

    iniset $SAHARA_CONF_FILE DEFAULT plugins $SAHARA_ENABLED_PLUGINS

    iniset $SAHARA_CONF_FILE database connection `database_connection_url sahara`

    if is_service_enabled neutron; then
        iniset $SAHARA_CONF_FILE DEFAULT use_neutron true

        if is_ssl_enabled_service "neutron" || is_service_enabled tls-proxy; then
            iniset $SAHARA_CONF_FILE neutron ca_file $SSL_BUNDLE_FILE
        fi
    else
        iniset $SAHARA_CONF_FILE DEFAULT use_neutron false
    fi

    if is_service_enabled heat && [ "$SAHARA_INFRA_ENGINE" == "heat" ]; then
        iniset $SAHARA_CONF_FILE DEFAULT infrastructure_engine heat

        if is_ssl_enabled_service "heat" || is_service_enabled tls-proxy; then
            iniset $SAHARA_CONF_FILE heat ca_file $SSL_BUNDLE_FILE
        fi
    else
        iniset $SAHARA_CONF_FILE DEFAULT infrastructure_engine direct
    fi

    if is_ssl_enabled_service "cinder" || is_service_enabled tls-proxy; then
        iniset $SAHARA_CONF_FILE cinder ca_file $SSL_BUNDLE_FILE
    fi

    if is_ssl_enabled_service "nova" || is_service_enabled tls-proxy; then
        iniset $SAHARA_CONF_FILE nova ca_file $SSL_BUNDLE_FILE
    fi

    if is_ssl_enabled_service "swift" || is_service_enabled tls-proxy; then
        iniset $SAHARA_CONF_FILE swift ca_file $SSL_BUNDLE_FILE
    fi

    if is_ssl_enabled_service "key" || is_service_enabled tls-proxy; then
        iniset $SAHARA_CONF_FILE keystone ca_file $SSL_BUNDLE_FILE
    fi

    # Register SSL certificates if provided
    if is_ssl_enabled_service sahara; then
        ensure_certificates SAHARA

        iniset $SAHARA_CONF_FILE ssl cert_file "$SAHARA_SSL_CERT"
        iniset $SAHARA_CONF_FILE ssl key_file "$SAHARA_SSL_KEY"
    fi

    iniset $SAHARA_CONF_FILE DEFAULT use_syslog $SYSLOG

    # Format logging
    if [ "$LOG_COLOR" == "True" ] && [ "$SYSLOG" == "False" ]; then
        setup_colorized_logging $SAHARA_CONF_FILE DEFAULT
    fi

    if is_service_enabled tls-proxy; then
        # Set the service port for a proxy to take the original
        iniset $SAHARA_CONF_FILE DEFAULT port $SAHARA_SERVICE_PORT_INT
    fi

    recreate_database sahara
    $SAHARA_BIN_DIR/sahara-db-manage --config-file $SAHARA_CONF_FILE upgrade head
}

# install_sahara() - Collect source and prepare
function install_sahara {
    setup_develop $SAHARA_DIR
}

# install_python_saharaclient() - Collect source and prepare
function install_python_saharaclient {
    if use_library_from_git "python-saharaclient"; then
        git_clone $SAHARACLIENT_REPO $SAHARACLIENT_DIR $SAHARACLIENT_BRANCH
        setup_develop $SAHARACLIENT_DIR
    fi
}

# start_sahara() - Start running processes, including screen
function start_sahara {
    local service_port=$SAHARA_SERVICE_PORT
    local service_protocol=$SAHARA_SERVICE_PROTOCOL
    if is_service_enabled tls-proxy; then
        service_port=$SAHARA_SERVICE_PORT_INT
        service_protocol="http"
    fi

    run_process sahara "$SAHARA_BIN_DIR/sahara-all --config-file $SAHARA_CONF_FILE"
    run_process sahara-api "$SAHARA_BIN_DIR/sahara-api --config-file $SAHARA_CONF_FILE"
    run_process sahara-eng "$SAHARA_BIN_DIR/sahara-engine --config-file $SAHARA_CONF_FILE"

    echo "Waiting for Sahara to start..."
    if ! wait_for_service $SERVICE_TIMEOUT $service_protocol://$SAHARA_SERVICE_HOST:$service_port; then
        die $LINENO "Sahara did not start"
    fi

    # Start proxies if enabled
    if is_service_enabled tls-proxy; then
        start_tls_proxy '*' $SAHARA_SERVICE_PORT $SAHARA_SERVICE_HOST $SAHARA_SERVICE_PORT_INT &
    fi
}

# stop_sahara() - Stop running processes
function stop_sahara {
    # Kill the Sahara screen windows
    stop_process sahara
    stop_process sahara-api
    stop_process sahara-eng
}

# Dispatcher for Sahara plugin
if is_service_enabled sahara; then
    if [[ "$1" == "stack" && "$2" == "install" ]]; then
        echo_summary "Installing sahara"
        install_sahara
        install_python_saharaclient
        cleanup_sahara
    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
        echo_summary "Configuring sahara"
        configure_sahara
        create_sahara_accounts
    elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
        echo_summary "Initializing sahara"
        start_sahara
    fi

    if [[ "$1" == "unstack" ]]; then
        stop_sahara
    fi

    if [[ "$1" == "clean" ]]; then
        cleanup_sahara
    fi
fi


# Restore xtrace
$XTRACE

# Local variables:
# mode: shell-script
# End:
