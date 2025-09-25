#!/usr/bin/env python3
"""
Setup script to pull the correct Ollama model for Iris.agent
"""

import subprocess
import sys

def run_command(command):
    """Run a command and return the result."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("🚀 Setting up Ollama for Iris.agent")
    print("=" * 50)
    
    # Check if Ollama is installed
    success, stdout, stderr = run_command("ollama --version")
    if not success:
        print("❌ Ollama is not installed or not in PATH")
        print("Please install Ollama from: https://ollama.ai/")
        sys.exit(1)
    
    print(f"✅ Ollama is installed: {stdout.strip()}")
    
    # Check if Ollama is running
    success, stdout, stderr = run_command("ollama list")
    if not success:
        print("❌ Ollama is not running")
        print("Please start Ollama service first")
        sys.exit(1)
    
    print("✅ Ollama is running")
    
    # Check available models
    success, stdout, stderr = run_command("ollama list")
    if success:
        print("\n📋 Currently available models:")
        print(stdout)
    
    # Pull llama3.2 if not available
    print("\n🔄 Pulling llama3.2 model...")
    success, stdout, stderr = run_command("ollama pull llama3.2")
    
    if success:
        print("✅ llama3.2 model pulled successfully!")
    else:
        print(f"❌ Failed to pull llama3.2: {stderr}")
        print("\n💡 You can try pulling other models:")
        print("   ollama pull llama3.1")
        print("   ollama pull llama2")
        print("   ollama pull mistral")
    
    # Show final model list
    print("\n📋 Final model list:")
    success, stdout, stderr = run_command("ollama list")
    if success:
        print(stdout)
    
    print("\n🎉 Setup complete! You can now use Iris.agent with local models.")

if __name__ == "__main__":
    main()
