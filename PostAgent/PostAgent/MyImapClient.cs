using System;
using MailKit.Net.Imap;
using MailKit;
using MimeKit;
using System.Diagnostics;

namespace PostAgent
{
    internal class MyImapClient
    {
        string email = "ratrumors@outlook.com";
        string password = "nSLsJhLK8QhV2t"; // Use an app password if MFA is enabled

        // Define IMAP server details
        string imapServer = "outlook.office365.com";
        int imapPort = 993; // IMAP over SSL

        public void GetEmail()
        {
            try
            {
                using (var client = new ImapClient())
                {
                    // Disable SSL validation if needed (not recommended in production)
                    client.ServerCertificateValidationCallback = (s, c, h, e) => true;

                    // Connect to the IMAP server
                    Console.WriteLine("Connecting to IMAP server...");
                    client.Connect(imapServer, imapPort, true);

                    // Authenticate
                    Console.WriteLine("Authenticating...");
                    client.Authenticate(email, password);

                    // Select the INBOX folder
                    var inbox = client.Inbox;
                    inbox.Open(FolderAccess.ReadOnly);

                    Console.WriteLine($"Total Messages: {inbox.Count}");
                    Console.WriteLine($"Unread Messages: {inbox.Unread}");

                    // Iterate through the messages
                    for (int i = 0; i < inbox.Count; i++)
                    {
                        var message = inbox.GetMessage(i);
                        Console.WriteLine($"Subject: {message.Subject}");
                        Console.WriteLine($"From: {message.From}");
                        Console.WriteLine($"Date: {message.Date}");
                        Console.WriteLine("Body Preview: " + message.TextBody?.Substring(0, Math.Min(100, message.TextBody.Length)));
                        Console.WriteLine(new string('-', 50));
                    }

                    // Disconnect
                    client.Disconnect(true);
                    Console.WriteLine("Disconnected.");
                }
            }
            catch (Exception ex)
            {
                Debug.WriteLine("An error occured");
                Debug.WriteLine(ex);
            }
        }
    }
}
