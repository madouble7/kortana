print("Testing Memory import...")
try:
    print("Successfully imported MemoryEntry from kortana.memory.memory")
except Exception as e:
    print(f"Error importing MemoryEntry: {e}")

print("\nTesting MemoryManager import...")
try:
    print("Successfully imported MemoryManager from kortana.memory.memory_manager")
except Exception as e:
    print(f"Error importing MemoryManager: {e}")

print("\nTesting Brain import...")
try:
    print("Successfully imported ChatEngine from kortana.core.brain")
except Exception as e:
    print(f"Error importing ChatEngine: {e}")
