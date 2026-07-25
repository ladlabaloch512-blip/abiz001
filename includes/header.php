<?php
require_once __DIR__ . '/brand-config.php';
require_once __DIR__ . '/products-config.php';

// Determine current page for active nav state
$current_page = basename($_SERVER['PHP_SELF']);
$page_title = isset($page_title) ? $page_title . $brand['meta_title_suffix'] : $brand['name'] . $brand['meta_title_suffix'];
$meta_desc = isset($meta_desc) ? $meta_desc : $brand['meta_description_default'];
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?php echo htmlspecialchars($page_title); ?></title>
    <meta name="description" content="<?php echo htmlspecialchars($meta_desc); ?>">

    <!-- SEO & Open Graph -->
    <link rel="canonical" href="https://<?php echo $_SERVER['HTTP_HOST'] . $_SERVER['REQUEST_URI']; ?>">
    <meta property="og:title" content="<?php echo htmlspecialchars($page_title); ?>">
    <meta property="og:description" content="<?php echo htmlspecialchars($meta_desc); ?>">
    <meta property="og:type" content="website">
    <meta property="og:image" content="assets/images/logos/logo.svg">
    <meta name="twitter:card" content="summary_large_image">

    <!-- Favicon -->
    <link rel="icon" type="image/svg+xml" href="<?php echo $brand['favicon_path']; ?>">

    <!-- Preconnect & Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">

    <!-- CSS -->
    <link rel="stylesheet" href="assets/css/variables.css">
    <link rel="stylesheet" href="assets/css/global.css">
    <link rel="stylesheet" href="assets/css/components.css">
    <link rel="stylesheet" href="assets/css/animations.css">
</head>
<body>

    <!-- Global Loader (Optional premium touch) -->
    <div class="loader-wrapper" id="global-loader">
        <div class="water-drop"></div>
    </div>

    <header class="site-header" id="site-header">
        <div class="container nav-container">
            <a href="index.php" class="logo-link" aria-label="<?php echo htmlspecialchars($brand['name']); ?> Home">
                <img src="<?php echo $brand['logo_path']; ?>" alt="<?php echo htmlspecialchars($brand['name']); ?> Logo" width="180" height="54">
            </a>

            <nav class="nav-menu" id="nav-menu">
                <a href="index.php" class="nav-link <?php echo $current_page == 'index.php' ? 'active' : ''; ?>">Home</a>
                <a href="about.php" class="nav-link <?php echo $current_page == 'about.php' ? 'active' : ''; ?>">About Us</a>
                <a href="products.php" class="nav-link <?php echo $current_page == 'products.php' ? 'active' : ''; ?>">Products</a>
                <a href="quality.php" class="nav-link <?php echo $current_page == 'quality.php' ? 'active' : ''; ?>">Quality</a>
                <a href="why-us.php" class="nav-link <?php echo $current_page == 'why-us.php' ? 'active' : ''; ?>">Why Us</a>
                <a href="contact.php" class="btn btn-primary" style="margin-left: 1rem;">Contact Us</a>
            </nav>

            <button class="mobile-menu-btn" id="mobile-menu-btn" aria-label="Toggle navigation menu">
                ☰
            </button>
        </div>
    </header>

    <main id="main-content">