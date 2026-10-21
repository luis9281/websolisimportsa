<?php
/**
 * Configuración del formulario de contacto.
 * Este archivo NO se puede abrir desde el navegador (lo bloquea .htaccess y la guarda de abajo).
 */
if (realpath($_SERVER['SCRIPT_FILENAME'] ?? '') === __FILE__) {
    http_response_code(403);
    exit;
}

return [
    // Destino de los mensajes
    'to_email'   => 'mercadeo@solisimportsa.com',

    // Remitente técnico: debe ser una cuenta de TU dominio (mejora la entrega y evita caer en spam).
    // Si no existe, créala en tu hosting (ej. no-responder@solisimportsa.com).
    'from_email' => 'no-responder@solisimportsa.com',
    'from_name'  => 'Sitio web Solis Import',

    // Anti-spam
    'min_seconds'   => 4,     // tiempo mínimo para llenar el formulario (los bots lo envían al instante)
    'max_seconds'   => 7200,  // la página caduca a las 2 horas
    'rate_limit'    => 3,     // máximo de envíos por IP...
    'rate_window'   => 600,   // ...cada 10 minutos
    'max_links'     => 1,     // enlaces permitidos en el mensaje

    // Cloudflare Turnstile (gratis, sin molestar al usuario). Déjalo vacío para desactivarlo.
    // Crea las llaves en https://dash.cloudflare.com/?to=/:account/turnstile
    'turnstile_site_key' => '',
    'turnstile_secret'   => '',

    // Valores permitidos (el servidor rechaza cualquier otro)
    'tipos' => ['Cotización', 'Suturas', 'Soporte y mantenimiento', 'Otro'],
    'marcas' => ['Otra o no estoy seguro', 'Atramat', 'Ferno', 'Ritter', 'Pega Medical', 'MyRay',
                 'Fanem', 'Novaerus', 'SurgiSeal', 'Brix3000', 'Sunset', 'Digitsole', 'Lasotronix', 'H.B. Fuller',
                 'TUR', 'Vcomin', 'Trulife', 'MIR', 'GV Health', 'Carestream Dental'],
];
