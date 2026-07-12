import base64

with open("logo_base64.txt", "r") as f:
    logo_b64 = f.read()

# Make the email layout look identical to the target screenshot (white background outside, slightly lighter gray/blue inside but no crazy gradient).
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Signature</title>
</head>
<body style="margin: 0; padding: 0;">
    <table cellpadding="0" cellspacing="0" border="0" style="font-family: Arial, sans-serif; max-width: 800px; width: 100%; background-color: #f6f8fb;">
        <tr>
            <td style="padding: 25px;">
                <table cellpadding="0" cellspacing="0" border="0" style="width: 100%;">
                    <tr>
                        <!-- Left Column: Logo -->
                        <td style="vertical-align: middle; width: 50%; padding-bottom: 20px;">
                            <img src="data:image/png;base64,{logo_b64}" alt="abiz" style="max-height: 80px; height: auto; display: block;">
                        </td>
                        <!-- Right Column: Social Icons -->
                        <td style="vertical-align: top; width: 50%; text-align: right; padding-bottom: 20px; padding-top: 15px;">
                            <table cellpadding="0" cellspacing="0" border="0" style="display: inline-block;">
                                <tr>
                                    <td style="padding: 0 5px;">
                                        <a href="#" style="text-decoration: none;"><img src="https://img.icons8.com/ios-filled/50/0970c8/facebook-new.png" alt="Facebook" style="width: 20px; height: 20px; display: block;"></a>
                                    </td>
                                    <td style="padding: 0 5px;">
                                        <a href="#" style="text-decoration: none;"><img src="https://img.icons8.com/ios-filled/50/0970c8/twitter.png" alt="Twitter" style="width: 20px; height: 20px; display: block;"></a>
                                    </td>
                                    <td style="padding: 0 5px;">
                                        <a href="#" style="text-decoration: none;"><img src="https://img.icons8.com/ios-filled/50/0970c8/linkedin.png" alt="LinkedIn" style="width: 20px; height: 20px; display: block;"></a>
                                    </td>
                                    <td style="padding: 0 5px;">
                                        <a href="#" style="text-decoration: none;"><img src="https://img.icons8.com/ios-filled/50/0970c8/instagram-new.png" alt="Instagram" style="width: 20px; height: 20px; display: block;"></a>
                                    </td>
                                    <td style="padding: 0 5px;">
                                        <a href="#" style="text-decoration: none;"><img src="https://img.icons8.com/ios-filled/50/0970c8/youtube-play.png" alt="YouTube" style="width: 20px; height: 20px; display: block;"></a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <!-- Left Column: Contact details -->
                        <td style="vertical-align: middle;">
                            <table cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td style="padding-bottom: 5px;">
                                        <img src="https://img.icons8.com/ios-filled/50/081b64/globe--v1.png" alt="Website" style="width: 16px; height: 16px; vertical-align: middle; margin-right: 8px;">
                                        <a href="https://abizglobalservices.com" style="color: #081b64; text-decoration: none; font-size: 14px; vertical-align: middle;">abizglobalservices.com</a>
                                    </td>
                                </tr>
                                <tr>
                                    <td>
                                        <img src="https://img.icons8.com/ios-filled/50/081b64/whatsapp--v1.png" alt="WhatsApp" style="width: 16px; height: 16px; vertical-align: middle; margin-right: 8px;">
                                        <a href="https://wa.me/923249476992" style="color: #081b64; text-decoration: none; font-size: 14px; vertical-align: middle;">+92 324 9476992</a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                        <!-- Right Column: Email -->
                        <td style="vertical-align: middle; text-align: right;">
                            <img src="https://img.icons8.com/ios-filled/50/081b64/new-post.png" alt="Email" style="width: 16px; height: 16px; vertical-align: middle; margin-right: 8px;">
                            <a href="mailto:contact@abizglobalservices.com" style="color: #081b64; text-decoration: none; font-size: 14px; vertical-align: middle;">contact@abizglobalservices.com</a>
                        </td>
                    </tr>
                </table>

                <!-- Disclaimer -->
                <table cellpadding="0" cellspacing="0" border="0" style="width: 100%; margin-top: 25px; border-top: 1px solid #dcdcdc; padding-top: 15px;">
                    <tr>
                        <td style="font-size: 11px; color: #666666; line-height: 1.4; text-align: left;">
                            <strong>Disclaimer:</strong> This email is from ABIZ Global Services, a digital marketing agency providing SEO, web, and app development solutions. If you wish to unsubscribe, please reply with "Unsubscribe".
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

with open("index.html", "w") as f:
    f.write(html_content)

print("Updated index.html layout")
