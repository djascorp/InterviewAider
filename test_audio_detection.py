#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script pour vérifier la détection audio avec musique en cours."""

import sys
import time
from audio_capture import capture_chunk, list_loopback_devices, compute_rms

# Fix encoding pour Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def test_audio_detection():
    """Test la capture audio avec RMS en temps réel."""
    print("=" * 60)
    print("TEST DE DÉTECTION AUDIO - Interview Assistant")
    print("=" * 60)
    
    # Lister les devices disponibles
    print("\n[1] Périphériques audio disponibles:")
    devices = list_loopback_devices()
    
    loopback_devices = [d for d in devices if d.get("is_loopback", False)]
    if loopback_devices:
        print(f"   ✓ {len(loopback_devices)} device(s) loopback détecté(s)")
        for d in loopback_devices:
            print(f"     - [{d['index']}] {d['name']} ({d['host_api']})")
        device_index = loopback_devices[0]['index']
    else:
        print("   ⚠ Aucun device loopback détecté, utilisation du device par défaut")
        device_index = None
    
    print(f"\n[2] Device sélectionné : {device_index}")
    print("[3] SEUIL RMS : 200")
    print("\n" + "=" * 60)
    print("DÉMARRAGE DU TEST (10 chunks de 3 secondes)")
    print("Mettez de la musique maintenant!")
    print("=" * 60)
    
    # Attendre que l'utilisateur démarre la musique
    print("\n⏳ Attente de 3 secondes pour démarrage...")
    time.sleep(3)
    
    detection_count = 0
    silence_count = 0
    
    for i in range(10):
        print(f"\n--- Chunk {i+1}/10 ---")
        print(f"⏱️  Capture de 3 secondes...")
        
        start_time = time.time()
        wav_bytes = capture_chunk(device_index)
        elapsed = time.time() - start_time
        
        if wav_bytes is None:
            silence_count += 1
            print(f"🔇 SILENCE détecté ( RMS < 200 )")
            print(f"   Temps: {elapsed:.1f}s | Silences: {silence_count} | Détections: {detection_count}")
        else:
            detection_count += 1
            print(f"🎵 AUDIO DÉTECTÉ! ( RMS >= 200 )")
            print(f"   Taille WAV: {len(wav_bytes)} bytes")
            print(f"   Temps: {elapsed:.1f}s | Silences: {silence_count} | Détections: {detection_count}")
            
            # Arrêter le test après détection
            print("\n" + "=" * 60)
            print("✅ TEST ARRÊTÉ - AUDIO DÉTECTÉ!")
            print("=" * 60)
            print(f"\nRésultats:")
            print(f"  • Chunks traités : {i+1}")
            print(f"  • Audio détecté : {detection_count} fois")
            print(f"  • Silences : {silence_count} fois")
            print(f" • Taux de détection : {detection_count/(i+1)*100:.1f}%")
            print(f"\n🎉 Le système fonctionne correctement!")
            return True
    
    # Test terminé sans détection
    print("\n" + "=" * 60)
    print("⚠️ TEST TERMINÉ - AUCUNE DÉTECTION")
    print("=" * 60)
    print(f"\nRésultats:")
    print(f"  • Chunks traités : 10")
    print(f"  • Audio détecté : {detection_count} fois")
    print(f"  • Silences : {silence_count} fois")
    print(f"\n💡 Suggestions:")
    print(f"  - Vérifiez que la musique est bien en cours")
    print(f"  - Vérifiez le device audio sélectionné")
    print(f"  - Augmentez le volume si nécessaire")
    print(f"  - Essayez un autre device audio")
    
    return False

if __name__ == "__main__":
    try:
        success = test_audio_detection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
