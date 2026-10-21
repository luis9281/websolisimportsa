<?php
declare(strict_types=1);
/**
 * Procesa el formulario de contacto de Solis Import S.A.
 *
 * Defensas: solo POST · mismo origen · token CSRF · campo trampa (honeypot) · tiempo mínimo ·
 * límite por IP · Cloudflare Turnstile (opcional) · validación estricta · listas permitidas ·
 * bloqueo de inyección de cabeceras · límite de enlaces · remitente fijo.
 */

$cfg = require __DIR__ . '/config.php';

header('X-Content-Type-Options: nosniff');
header('Cache-Control: no-store');
header('Referrer-Policy: same-origin');

$isAjax = (($_SERVER['HTTP_X_REQUESTED_WITH'] ?? '') === 'fetch');

function respond(bool $ok, string $message, array $errors = [], int $code = 200): void
{
    global $isAjax;
    if ($isAjax) {
        http_response_code($code);
        header('Content-Type: application/json; charset=utf-8');
        echo json_encode(['ok' => $ok, 'message' => $message, 'errors' => $errors], JSON_UNESCAPED_UNICODE);
        exit;
    }
    header('Location: ./?' . ($ok ? 'enviado=1' : 'error=' . rawurlencode($message)) . '#formulario');
    exit;
}

function clean(string $v): string
{
    $v = trim($v);
    $v = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', $v) ?? '';
    return $v;
}

function one_line(string $v): string
{
    return trim(preg_replace('/[\r\n\t]+/', ' ', $v) ?? '');
}

// 1) Método
if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    http_response_code(405);
    header('Allow: POST');
    exit;
}

// 2) Sesión (misma configuración que index.php)
session_set_cookie_params([
    'lifetime' => 0, 'path' => '/', 'httponly' => true, 'samesite' => 'Lax',
    'secure' => (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off'),
]);
session_start();

// 3) Mismo origen
$host = $_SERVER['HTTP_HOST'] ?? '';
foreach (['HTTP_ORIGIN', 'HTTP_REFERER'] as $h) {
    if (!empty($_SERVER[$h])) {
        $oh = parse_url((string)$_SERVER[$h], PHP_URL_HOST);
        $hh = parse_url('http://' . $host, PHP_URL_HOST);
        if ($oh !== null && $hh !== null && strcasecmp((string)$oh, (string)$hh) !== 0) {
            respond(false, 'Solicitud no permitida.', [], 403);
        }
        break;
    }
}

// 4) CSRF
$token = (string)($_POST['csrf'] ?? '');
if ($token === '' || !hash_equals((string)($_SESSION['csrf'] ?? ''), $token)) {
    respond(false, 'La página caducó. Recárgala e inténtalo de nuevo.', [], 403);
}

// 5) Honeypot: un humano nunca ve este campo. Fingimos éxito para no darle pistas al bot.
if (trim((string)($_POST['sitio_web'] ?? '')) !== '') {
    respond(true, 'Mensaje enviado.');
}

// 6) Tiempo de llenado
$elapsed = time() - (int)($_SESSION['form_ts'] ?? 0);
if ($elapsed < (int)$cfg['min_seconds']) {
    respond(false, 'Enviaste el formulario demasiado rápido. Espera un momento e inténtalo otra vez.', [], 429);
}
if ($elapsed > (int)$cfg['max_seconds']) {
    respond(false, 'La página caducó. Recárgala e inténtalo de nuevo.', [], 403);
}

// 7) Límite por IP (archivo temporal, sin base de datos)
$ip = $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
$rlFile = sys_get_temp_dir() . '/solis_rl_' . sha1($ip) . '.json';
$now = time();
$hits = [];
if (is_file($rlFile)) {
    $hits = json_decode((string)file_get_contents($rlFile), true) ?: [];
    $hits = array_values(array_filter($hits, fn($t) => is_int($t) && $t > $now - (int)$cfg['rate_window']));
}
if (count($hits) >= (int)$cfg['rate_limit']) {
    respond(false, 'Has enviado varios mensajes seguidos. Intenta de nuevo en unos minutos o escríbenos por WhatsApp.', [], 429);
}

// 8) Turnstile (si está configurado)
if ($cfg['turnstile_secret'] !== '') {
    $resp = (string)($_POST['cf-turnstile-response'] ?? '');
    $okCaptcha = false;
    if ($resp !== '') {
        $ctx = stream_context_create(['http' => [
            'method' => 'POST', 'timeout' => 8,
            'header' => "Content-Type: application/x-www-form-urlencoded\r\n",
            'content' => http_build_query(['secret' => $cfg['turnstile_secret'], 'response' => $resp, 'remoteip' => $ip]),
        ]]);
        $raw = @file_get_contents('https://challenges.cloudflare.com/turnstile/v0/siteverify', false, $ctx);
        $okCaptcha = $raw !== false && (json_decode($raw, true)['success'] ?? false) === true;
    }
    if (!$okCaptcha) {
        respond(false, 'No pudimos verificar que eres una persona. Inténtalo de nuevo.', [], 403);
    }
}

// 9) Validación
$tipo     = one_line(clean((string)($_POST['tipo'] ?? '')));
$nombre   = one_line(clean((string)($_POST['nombre'] ?? '')));
$empresa  = one_line(clean((string)($_POST['empresa'] ?? '')));
$correo   = one_line(clean((string)($_POST['correo'] ?? '')));
$telefono = one_line(clean((string)($_POST['telefono'] ?? '')));
$marca    = one_line(clean((string)($_POST['marca'] ?? '')));
$mensaje  = clean((string)($_POST['mensaje'] ?? ''));
$acepto   = ($_POST['acepto'] ?? '') === '1';

$errors = [];
if (!in_array($tipo, $cfg['tipos'], true))                     $errors['tipo'] = 'Elige qué necesitas.';
if (mb_strlen($nombre) < 2 || mb_strlen($nombre) > 80)         $errors['nombre'] = 'Escribe tu nombre.';
if (mb_strlen($empresa) < 2 || mb_strlen($empresa) > 100)      $errors['empresa'] = 'Escribe el nombre de tu empresa o institución.';
if (!filter_var($correo, FILTER_VALIDATE_EMAIL) || mb_strlen($correo) > 120) $errors['correo'] = 'Escribe un correo válido.';
if ($telefono !== '' && !preg_match('/^[0-9+()\-\s.]{6,25}$/', $telefono)) $errors['telefono'] = 'Usa solo números, espacios, + o guiones.';
if (!in_array($marca, $cfg['marcas'], true))                   $errors['marca'] = 'Elige una opción de la lista.';
if (mb_strlen($mensaje) < 10 || mb_strlen($mensaje) > 1500)    $errors['mensaje'] = 'Cuéntanos tu consulta (entre 10 y 1500 caracteres).';
if (!$acepto)                                                  $errors['acepto'] = 'Debes aceptar el uso de tus datos para responderte.';
if (preg_match_all('~https?://|www\.~i', $mensaje) > (int)$cfg['max_links'] || preg_match('~<\s*a\s|\[url~i', $mensaje)) {
    $errors['mensaje'] = 'Por seguridad, el mensaje no puede incluir enlaces.';
}
if ($errors) {
    respond(false, 'Revisa los campos marcados.', $errors, 422);
}

// 10) Correo
$subject = 'Web: ' . $tipo . ' – ' . $nombre . ($marca !== 'Otra o no estoy seguro' ? ' (' . $marca . ')' : '');
$body  = "Nuevo mensaje desde el sitio web\n";
$body .= str_repeat('-', 40) . "\n";
$body .= "Necesita:  $tipo\nMarca:     $marca\n";
$body .= "Nombre:    $nombre\nEmpresa:   " . ($empresa ?: '-') . "\n";
$body .= "Correo:    $correo\nTeléfono:  " . ($telefono ?: '-') . "\n";
$body .= str_repeat('-', 40) . "\n\n$mensaje\n\n";
$body .= str_repeat('-', 40) . "\nEnviado: " . date('d/m/Y H:i') . ' (hora del servidor)  ·  IP: ' . $ip . "\n";

$fromName = mb_encode_mimeheader($cfg['from_name'], 'UTF-8', 'B');
$replyName = mb_encode_mimeheader($nombre, 'UTF-8', 'B');
$headers = [
    'From: ' . $fromName . ' <' . $cfg['from_email'] . '>',
    'Reply-To: ' . $replyName . ' <' . $correo . '>',
    'MIME-Version: 1.0',
    'Content-Type: text/plain; charset=UTF-8',
    'Content-Transfer-Encoding: 8bit',
    'X-Mailer: SolisWebForm/1.0',
];

$sent = @mail($cfg['to_email'], mb_encode_mimeheader($subject, 'UTF-8', 'B'), $body, implode("\r\n", $headers),
              '-f' . $cfg['from_email']);

if (!$sent) {
    error_log('[solis-form] mail() devolvió false');
    respond(false, 'No pudimos enviar el mensaje en este momento. Escríbenos por WhatsApp o por correo directamente.', [], 500);
}

// 11) Éxito: registrar el envío, renovar el token y reiniciar el reloj
$hits[] = $now;
@file_put_contents($rlFile, json_encode($hits), LOCK_EX);
$_SESSION['csrf'] = bin2hex(random_bytes(32));
$_SESSION['form_ts'] = time();

respond(true, 'Gracias, ' . $nombre . '. Recibimos tu mensaje y te responderemos pronto.');
