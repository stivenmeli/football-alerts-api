#!/usr/bin/env python3
"""Script to get your Telegram chat ID."""

import asyncio
import httpx
import sys


async def get_chat_id(bot_token: str) -> None:
    """Get chat ID from recent messages."""
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("ok"):
                print("❌ Error: Invalid bot token or API error")
                return
            
            updates = data.get("result", [])
            
            if not updates:
                print("⚠️  No hay mensajes recientes.")
                print("\n📝 Por favor:")
                print("1. Abre Telegram")
                print("2. Busca tu bot")
                print("3. Envíale cualquier mensaje (ejemplo: 'hola')")
                print("4. Ejecuta este script nuevamente")
                return
            
            print("✅ Mensajes encontrados!\n")
            
            # Get unique chat IDs
            chat_ids = set()
            for update in updates:
                message = update.get("message", {})
                chat = message.get("chat", {})
                chat_id = chat.get("id")
                username = chat.get("username", "Sin username")
                first_name = chat.get("first_name", "Sin nombre")
                
                if chat_id:
                    chat_ids.add((chat_id, username, first_name))
            
            print("📱 Chat IDs encontrados:")
            print("-" * 60)
            for chat_id, username, first_name in chat_ids:
                print(f"Chat ID: {chat_id}")
                print(f"Usuario: @{username}")
                print(f"Nombre: {first_name}")
                print("-" * 60)
            
            if len(chat_ids) == 1:
                the_chat_id = list(chat_ids)[0][0]
                print(f"\n✅ Tu TELEGRAM_CHAT_ID es: {the_chat_id}")
                print(f"\n📋 Copia este valor al archivo .env:")
                print(f"TELEGRAM_CHAT_ID={the_chat_id}")
    
    except Exception as e:
        print(f"❌ Error: {e}")


async def main() -> None:
    """Main function."""
    print("🤖 Telegram Chat ID Finder\n")
    
    if len(sys.argv) > 1:
        bot_token = sys.argv[1]
    else:
        bot_token = input("Ingresa tu BOT TOKEN de Telegram: ").strip()
    
    if not bot_token:
        print("❌ Error: Bot token es requerido")
        return
    
    await get_chat_id(bot_token)


if __name__ == "__main__":
    asyncio.run(main())

