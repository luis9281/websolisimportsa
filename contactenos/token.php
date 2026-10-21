<?php
declare(strict_types=1);
/**
 * Entrega al formulario su token CSRF y arranca el reloj anti-bot.
 * La página de contacto es HTML estático; este archivo es lo único que necesita sesión.
 */
$cfg = require __DIR__ . '/config.php';

session_set_cookie_params([
    'lifetime' => 0, 'path' => '/', 'httponly' => true, 'samesite' => 'Lax',
    'secure' => (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off'),
]);
session_start();

$_SESSION['csrf'] = bin2hex(random_bytes(32));
$_SESSION['form_ts'] = time();

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

echo json_encode([
    'csrf' => $_SESSION['csrf'],
    'turnstile' => (string)$cfg['turnstile_site_key'],
]);
