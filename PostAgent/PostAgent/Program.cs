// See https://aka.ms/new-console-template for more information
using PostAgent;

Console.WriteLine("PostAgent is here!");

var client = new MyImapClient();
client.GetEmail();
