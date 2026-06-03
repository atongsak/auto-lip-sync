# Handles phoneme tokens composed of multiple chars
def normalize_token(token: str) -> list[str]:
    if not token:
        return []

    token = token.strip()

    # Map syllabic consonants to base consonant
    if token in ["n̩", "l̩", "m̩"]:
        return [token[0]]

    # Rare combined tokens
    if token == "əl":
        return ["ə", "l"]

    # Split vowel+r if combined
    if token.endswith("ɹ") and len(token) > 1:
        return [token[:-1], "ɹ"]

    return [token]

# Cleans viseme list and stores into keyframe dict
def cleanup_visemes(visemes, viseme_mapping, settings_dict):
    render_start = settings_dict["render_start"]
    render_end = settings_dict["render_end"]
    mouth_close_delay = settings_dict["mouth_close_delay"]
    
    cleaned = []
    current_frame = render_start

    for v in visemes:
        start_frame = v["start"] 
        end_frame = v["end"]
        token = v["token"]

        # Length marker: extend previous viseme
        if token == "length_marker":
            if cleaned:
                cleaned[-1]["end"] = max(cleaned[-1]["end"], end_frame)
            continue

        # Gap
        if token == "gap":
            duration = end_frame - start_frame

            if duration > mouth_close_delay:
                sil_start = start_frame + mouth_close_delay

                if cleaned:
                    cleaned[-1]["end"] = sil_start

                cleaned.append({
                    "token": "sil",
                    "viseme": viseme_mapping["sil"],
                    "start": sil_start,
                    "end": end_frame
                })

            current_frame = end_frame
            continue

        # If gap between visemes, insert sil
        if start_frame > current_frame + mouth_close_delay:
            hold_end = current_frame + mouth_close_delay

            # Extend previous viseme hold
            if cleaned:
                cleaned[-1]["end"] = hold_end

            cleaned.append({
                "token": "sil",
                "viseme": viseme_mapping["sil"],
                "start": hold_end,
                "end": start_frame
            })
        
        # Append viseme
        cleaned.append({
            "token": v["token"],
            "viseme": v["viseme"],
            "start": start_frame,
            "end": end_frame
        })

        current_frame = max(current_frame, end_frame)
      
    # Trailing sil
    if current_frame < render_end:
        start = current_frame + mouth_close_delay

        if start < render_end:
            cleaned.append({
                "token": "sil",
                "viseme": viseme_mapping["sil"],
                "start": start,
                "end": render_end
            })

    return {"keyframes": cleaned}

# Creates a viseme timing list using phoneme timing data
def phonemes_to_visemes(phoneme_timings, viseme_mapping, settings_dict):
    render_start = settings_dict["render_start"]
    fps = settings_dict["fps"]
    results = []

    for p in phoneme_timings:
        raw_token = p["char"]

        # Convert phoneme timing from seconds to frames, taking into account render start
        start = (p["start"] * fps) + render_start
        end = (p["end"] * fps) + render_start

        # Handle multi-char phoneme tokens
        tokens = normalize_token(raw_token)

        for token in tokens:
            # Whitespace becomes explicit marker
            if token == "":
                results.append({
                    "token": "gap",
                    "viseme": None,
                    "start": start,
                    "end": end
                })
                continue

            # Preserve length marker
            if token == "ː":
                results.append({
                    "token": "length_marker",
                    "viseme": None,
                    "start": start,
                    "end": end
                })
                continue

            viseme = viseme_mapping.get(token)

            if viseme is None:
                continue

            results.append({
                "token": token,
                "viseme": viseme,
                "start": start,
                "end": end
            })

    return results