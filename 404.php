<?php
$page_title = "Page Not Found";
require_once __DIR__ . '/includes/header.php';
?>

<section class="section" style="padding-top: 150px; min-height: 80vh; display: flex; align-items: center; justify-content: center; text-align: center;">
    <div class="container reveal">
        <h1 style="font-size: 8rem; color: var(--color-secondary); margin-bottom: 0;">404</h1>
        <h2 style="font-size: var(--text-h3); margin-bottom: 1.5rem;">Oops! The page you're looking for has evaporated.</h2>
        <p style="max-width: 500px; margin: 0 auto 2rem;">It seems we can't find the page you are looking for. It might have been removed, had its name changed, or is temporarily unavailable.</p>
        <a href="index.php" class="btn btn-primary">Return Home</a>
    </div>
</section>

<?php require_once __DIR__ . '/includes/footer.php'; ?>