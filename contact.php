<?php
session_start();

// Generate CSRF token if not set
if (empty($_SESSION['csrf_token'])) {
    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
}

$page_title = "Contact Us";

// Pre-fill subject if passed via GET parameter
$prefilled_subject = isset($_GET['subject']) ? htmlspecialchars($_GET['subject']) : '';

require_once __DIR__ . '/includes/header.php';
?>

<section class="section section-bg-light" style="padding-top: 150px;">
    <div class="container">
        <div class="section-header reveal">
            <h1 style="font-size: var(--text-h2);">Get in Touch</h1>
            <p>We're here to answer any questions you may have about our products, deliveries, or corporate partnerships.</p>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1.5fr; gap: var(--spacing-xl); margin-top: var(--spacing-lg);">

            <!-- Contact Info -->
            <div class="reveal">
                <div class="card" style="margin-bottom: var(--spacing-md); background: var(--color-primary); color: white;">
                    <h3 style="color: white; margin-bottom: 1.5rem;">Contact Information</h3>

                    <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem;">
                        <span style="font-size: 1.5rem;">📍</span>
                        <div>
                            <strong style="display: block; margin-bottom: 0.25rem;">Address</strong>
                            <p style="margin: 0; color: rgba(255,255,255,0.8);"><?php echo htmlspecialchars($brand['address_line_1']); ?><br><?php echo htmlspecialchars($brand['address_line_2']); ?></p>
                        </div>
                    </div>

                    <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem;">
                        <span style="font-size: 1.5rem;">📞</span>
                        <div>
                            <strong style="display: block; margin-bottom: 0.25rem;">Phone</strong>
                            <p style="margin: 0;"><a href="tel:<?php echo htmlspecialchars($brand['phone']); ?>" style="color: rgba(255,255,255,0.8);"><?php echo htmlspecialchars($brand['phone']); ?></a></p>
                        </div>
                    </div>

                    <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem;">
                        <span style="font-size: 1.5rem;">💬</span>
                        <div>
                            <strong style="display: block; margin-bottom: 0.25rem;">WhatsApp</strong>
                            <p style="margin: 0;"><a href="https://wa.me/<?php echo htmlspecialchars($brand['whatsapp']); ?>" style="color: rgba(255,255,255,0.8);" target="_blank">Message Us</a></p>
                        </div>
                    </div>

                    <div style="display: flex; gap: 1rem;">
                        <span style="font-size: 1.5rem;">✉️</span>
                        <div>
                            <strong style="display: block; margin-bottom: 0.25rem;">Email</strong>
                            <p style="margin: 0;"><a href="mailto:<?php echo htmlspecialchars($brand['email']); ?>" style="color: rgba(255,255,255,0.8);"><?php echo htmlspecialchars($brand['email']); ?></a></p>
                        </div>
                    </div>
                </div>

                <div class="card" style="padding: 0; overflow: hidden; height: 250px;">
                    <iframe src="<?php echo $brand['google_maps_embed']; ?>" width="100%" height="100%" style="border:0;" allowfullscreen="" loading="lazy"></iframe>
                </div>
            </div>

            <!-- Contact Form -->
            <div class="reveal delay-200">
                <div class="card" style="padding: var(--spacing-lg);">
                    <h3 style="margin-bottom: 1.5rem;">Send us a Message</h3>

                    <div id="form-message" style="display: none; padding: 1rem; border-radius: var(--border-radius-md); margin-bottom: 1.5rem; font-weight: 500;"></div>

                    <form id="contact-form" action="includes/mail-handler.php" method="POST">
                        <input type="hidden" name="csrf_token" value="<?php echo $_SESSION['csrf_token']; ?>">

                        <!-- Honeypot field (hidden from users) to prevent spam -->
                        <div style="display:none;">
                            <label>Leave this field blank</label>
                            <input type="text" name="website_url_hp" tabindex="-1" autocomplete="off">
                        </div>

                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
                            <div>
                                <label for="name" style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Full Name *</label>
                                <input type="text" id="name" name="name" required placeholder="John Doe">
                            </div>
                            <div>
                                <label for="phone" style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Phone Number</label>
                                <input type="tel" id="phone" name="phone" placeholder="+1 (555) 000-0000">
                            </div>
                        </div>

                        <div style="margin-bottom: 1rem;">
                            <label for="email" style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Email Address *</label>
                            <input type="email" id="email" name="email" required placeholder="john@example.com">
                        </div>

                        <div style="margin-bottom: 1rem;">
                            <label for="subject" style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Subject</label>
                            <input type="text" id="subject" name="subject" placeholder="How can we help?" value="<?php echo $prefilled_subject; ?>">
                        </div>

                        <div style="margin-bottom: 1.5rem;">
                            <label for="message" style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Message *</label>
                            <textarea id="message" name="message" rows="5" required placeholder="Your message here..."></textarea>
                        </div>

                        <button type="submit" class="btn btn-primary" id="submit-btn" style="width: 100%;">
                            <span>Send Message</span>
                        </button>
                    </form>
                </div>
            </div>

        </div>
    </div>
</section>

<!-- Include AJAX Script for Form Submission -->
<script>
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('contact-form');
    const formMessage = document.getElementById('form-message');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = submitBtn.querySelector('span');

    if(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            // UI Loading State
            submitBtn.disabled = true;
            btnText.textContent = 'Sending...';
            formMessage.style.display = 'none';

            const formData = new FormData(form);

            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'Accept': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                formMessage.style.display = 'block';
                formMessage.textContent = data.message;

                if(data.status === 'success') {
                    formMessage.style.backgroundColor = '#d4edda';
                    formMessage.style.color = '#155724';
                    formMessage.style.border = '1px solid #c3e6cb';
                    form.reset(); // Clear form on success
                } else {
                    formMessage.style.backgroundColor = '#f8d7da';
                    formMessage.style.color = '#721c24';
                    formMessage.style.border = '1px solid #f5c6cb';
                }
            })
            .catch(error => {
                formMessage.style.display = 'block';
                formMessage.style.backgroundColor = '#f8d7da';
                formMessage.style.color = '#721c24';
                formMessage.style.border = '1px solid #f5c6cb';
                formMessage.textContent = 'An error occurred. Please try again later.';
            })
            .finally(() => {
                submitBtn.disabled = false;
                btnText.textContent = 'Send Message';
            });
        });
    }
});
</script>

<?php require_once __DIR__ . '/includes/footer.php'; ?>