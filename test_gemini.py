#!/usr/bin/env python3
"""
Test script for Gemini AI integration

This script tests the basic functionality of the Gemini client
without requiring a full Flask application startup.
"""
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.gemini_client import GeminiConfig, GeminiClient


def test_gemini_client():
    """Test basic Gemini client functionality."""
    print("🚀 Testing Gemini AI Client...")
    
    # Check if API key is available
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment variables")
        print("ℹ️  Please set your Gemini API key in the .env file")
        return False
    
    try:
        # Create configuration
        config = GeminiConfig(
            api_key=api_key,
            model_name="gemini-pro",
            temperature=0.7
        )
        
        # Initialize client
        client = GeminiClient(config)
        print("✅ Gemini client initialized successfully")
        
        # Test basic text generation
        print("\n📝 Testing text generation...")
        response = client.generate_text("Hello! Please respond with a brief greeting.")
        
        if response.success:
            print(f"✅ Text generation successful!")
            print(f"📄 Response: {response.content}")
        else:
            print(f"❌ Text generation failed: {response.error_message}")
            return False
        
        # Test health check
        print("\n🔍 Testing health check...")
        health_status = client.health_check()
        
        if health_status:
            print("✅ Health check passed")
        else:
            print("❌ Health check failed")
            return False
        
        print("\n🎉 All tests passed! Gemini integration is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Gemini client: {e}")
        return False


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    success = test_gemini_client()
    
    if success:
        print("\n✨ Gemini AI integration is ready for use!")
        sys.exit(0)
    else:
        print("\n💥 Gemini AI integration test failed!")
        sys.exit(1)
