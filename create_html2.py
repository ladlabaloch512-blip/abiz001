import base64
import re

with open("logo_base64.txt", "r") as f:
    logo_b64 = f.read()

# I will also adjust the HTML so the background doesn't show gradient outside the body, or just keep it simple.
# The previous version had a gradient. The user's screenshot had a white body but light gradient in the table.
# I'll update the twitter icon since X seems broken in the original screenshot (icons8 link maybe failed or needs update).
# Actually, I'll just change the twitter icon to standard twitter.

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Signature</title>
</head>
<body style="margin: 0; padding: 0;">
    <table cellpadding="0" cellspacing="0" border="0" style="font-family: Arial, sans-serif; max-width: 800px; width: 100%; background-color: #ffffff; background-image: linear-gradient(to right, #ffffff, #e6f2ff);">
        <tr>
            <td style="padding: 30px;">
                <table cellpadding="0" cellspacing="0" border="0" style="width: 100%;">
                    <tr>
                        <!-- Left Column: Logo -->
                        <td style="vertical-align: middle; width: 60%; padding-bottom: 20px;">
                            <img src="data:image/png;base64,{logo_b64}" alt="abiz" style="max-height: 70px; height: auto; display: block;">
                        </td>
                        <!-- Right Column: Social Icons -->
                        <td style="vertical-align: bottom; width: 40%; text-align: right; padding-bottom: 20px;">
                            <table cellpadding="0" cellspacing="0" border="0" style="display: inline-block;">
                                <tr>
                                    <td style="padding: 0 5px;">
                                        <a href="#" style="text-decoration: none;"><img src="https://img.icons8.com/ios-filled/50/0970c8/facebook-new.png" alt="Facebook" style="width: 24px; height: 24px; display: block;"></a>
                                    </td>
                                    <td style="padding: 0 5px;">
                                        <a href="#" style="text-decoration: none;"><img src="https://img.icons8.com/ios-filled/50/0970c8/twitter.png" alt="Twitter" style="width: 24px; height: 24px; display: block;"></a>
                                    </td>
                                    <td style="padding: 0 5px;">
                                        <a href="#" style="text-decoration: none;"><img src="https://img.icons8.com/ios-filled/50/0970c8/linkedin.png" alt="LinkedIn" style="width: 24px; height: 24px; display: block;"></a>
                                    </td>
                                    <td style="padding: 0 5px;">
                                        <a href="#" style="text-decoration: none;"><img src="https://img.icons8.com/ios-filled/50/0970c8/instagram-new.png" alt="Instagram" style="width: 24px; height: 24px; display: block;"></a>
                                    </td>
                                    <td style="padding: 0 5px;">
                                        <a href="#" style="text-decoration: none;"><img src="https://img.icons8.com/ios-filled/50/0970c8/youtube-play.png" alt="YouTube" style="width: 24px; height: 24px; display: block;"></a>
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
                                    <td style="padding-bottom: 8px;">
                                        <img src="https://img.icons8.com/ios-filled/50/081b64/globe--v1.png" alt="Website" style="width: 18px; height: 18px; vertical-align: middle; margin-right: 8px;">
                                        <a href="https://abizglobalservices.com" style="color: #081b64; text-decoration: none; font-size: 15px; vertical-align: middle;">abizglobalservices.com</a>
                                    </td>
                                </tr>
                                <tr>
                                    <td>
                                        <img src="https://img.icons8.com/ios-filled/50/081b64/whatsapp--v1.png" alt="WhatsApp" style="width: 18px; height: 18px; vertical-align: middle; margin-right: 8px;">
                                        <a href="https://wa.me/923249476992" style="color: #081b64; text-decoration: none; font-size: 15px; vertical-align: middle;">+92 324 9476992</a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                        <!-- Right Column: Email -->
                        <td style="vertical-align: middle; text-align: right;">
                            <img src="https://img.icons8.com/ios-filled/50/081b64/new-post.png" alt="Email" style="width: 20px; height: 20px; vertical-align: middle; margin-right: 8px;">
                            <a href="mailto:contact@abizglobalservices.com" style="color: #081b64; text-decoration: none; font-size: 16px; vertical-align: middle;">contact@abizglobalservices.com</a>
                        </td>
                    </tr>
                </table>

                <!-- Disclaimer -->
                <table cellpadding="0" cellspacing="0" border="0" style="width: 100%; margin-top: 30px; border-top: 1px solid #cccccc; padding-top: 15px;">
                    <tr>
                        <td style="font-size: 11px; color: #666666; line-height: 1.4; text-align: left;">
                            <strong>Disclaimer:</strong> This email is intended for business growth purposes; reply with "Unsubscribe" to opt out.
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

print("Updated index.html with shortened disclaimer")
