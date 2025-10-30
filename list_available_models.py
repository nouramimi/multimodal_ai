import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

def list_gemini_models():
    
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ ERREUR: GEMINI_API_KEY non trouvée dans .env")
        print("Ajoutez votre clé API dans le fichier .env")
        return
    
    print("🔑 Clé API trouvée!")
    print("=" * 80)
    
    genai.configure(api_key=api_key)
    
    print("📋 LISTE DES MODÈLES GEMINI DISPONIBLES:")
    print("=" * 80)
    
    try:
        models = genai.list_models()
        
        generation_models = []
        
        for model in models:
            print(f"\n📦 Modèle: {model.name}")
            print(f"   Display Name: {model.display_name}")
            print(f"   Description: {model.description}")
            print(f"   Supported Methods: {model.supported_generation_methods}")
            
            if 'generateContent' in model.supported_generation_methods:
                generation_models.append(model.name)
                print("   ✅ Supporte generateContent (Compatible avec votre chatbot)")
            else:
                print("   ❌ Ne supporte pas generateContent")
            
            print("-" * 80)
        
        print("\n" + "=" * 80)
        print("🎯 MODÈLES COMPATIBLES AVEC VOTRE CHATBOT:")
        print("=" * 80)
        
        if generation_models:
            for i, model_name in enumerate(generation_models, 1):
                
                clean_name = model_name.replace("models/", "")
                print(f"{i}. {clean_name}")
                
                if "flash" in clean_name.lower():
                    print("   💡 Recommandé pour: Vitesse et efficacité")
                elif "pro" in clean_name.lower():
                    print("   💡 Recommandé pour: Tâches complexes et précision")
        else:
            print("❌ Aucun modèle compatible trouvé")
        
        print("\n" + "=" * 80)
        print("💡 POUR UTILISER UN MODÈLE DANS VOTRE CODE:")
        print("=" * 80)
        print("\nDans chatbot_orchestrator.py, utilisez:")
        print('model="gemini-1.5-flash-latest"  # Ou un autre nom de la liste ci-dessus')
        
    except Exception as e:
        print(f"\n❌ ERREUR lors de la récupération des modèles:")
        print(f"   {str(e)}")
        print("\n💡 Vérifiez que votre clé API est valide et active")
        print("   Obtenez une clé sur: https://makersuite.google.com/app/apikey")


if __name__ == "__main__":
    print("🚀 Script de liste des modèles Gemini")
    print("=" * 80)
    list_gemini_models()
    print("\n✅ Script terminé")