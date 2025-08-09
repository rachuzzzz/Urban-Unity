import urllib.parse

# Enter your actual MongoDB Atlas password here
password = input("Enter your MongoDB Atlas password: ")
encoded_password = urllib.parse.quote_plus(password)

print(f"\n✅ Encoded password: {encoded_password}")
print(f"\n📝 Update your .env file with this line:")
print(f"MONGODB_URI=mongodb+srv://thomasraisen123:{encoded_password}@cluster0.9lctmkp.mongodb.net/urbanunity?retryWrites=true&w=majority&appName=Cluster0")