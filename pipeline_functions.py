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


def cleanup_visemes(visemes, viseme_mapping, render_end, mouth_close_delay):
    if not visemes:
        return []
    
    visemes = sorted(visemes, key=lambda x: x["start"])

    cleaned = []
    current_frame = 0

    for v in visemes:
        # If gap between visemes, insert sil
        if v["start"] > current_frame + mouth_close_delay:
            hold_end = current_frame + mouth_close_delay

            # extend previous viseme hold
            if cleaned:
                cleaned[-1]["end"] = hold_end

            cleaned.append({
                "token": "sil",
                "viseme": viseme_mapping["sil"],
                "start": hold_end,
                "end": v["start"]
            })
        
        # Append viseme
        cleaned.append(v)
        current_frame = max(current_frame, v["end"])

    # Trailing sil
    if current_frame < render_end:
        cleaned.append({
            "token": "sil",
            "viseme": viseme_mapping["sil"],
            "start": current_frame + mouth_close_delay,
            "end": render_end
        })

    return cleaned


def phonemes_to_visemes(phoneme_timings, viseme_mapping, strip_start, settings_dict):
    fps = settings_dict["fps"]
    mouth_close_delay = settings_dict["mouth_close_delay"]

    results = []

    for p in phoneme_timings:
        raw_token = p["char"]
        start = (p["start"] + strip_start) * fps
        end = (p["end"] + strip_start) * fps

        tokens = normalize_token(raw_token)

        for token in tokens:
            # Handle silence
            if token == "":                
                if start is None or end is None:
                    continue

                duration = end - start
    
                # Short pause → blend into previous viseme
                if results and duration < mouth_close_delay:
                    results[-1]["end"] = end 
                    continue

                sil_start = start + mouth_close_delay
                viseme = viseme_mapping.get("sil")

                if sil_start >= end:
                    def_start = start
                else:
                    def_start = sil_start

                results.append({
                    "token": "sil",
                    "viseme": viseme,
                    "start": def_start,
                    "end": end
                })
                continue

            # Handle length marker
            elif token == "ː":
                if results:
                    results[-1]["end"] = max(results[-1]["end"], end)
                continue

            # Handle normal phonemes
            else:
                viseme = viseme_mapping.get(token)

                if viseme is None:
                    # Debug but don't crash pipeline
                    if token != "":
                        print(f"No viseme for: {token}")
                    continue

            results.append({
                "token": token,
                "viseme": viseme,
                "start": start,
                "end": end
            })

    return results
    # return cleanup_visemes(results, viseme_mapping, render_end, mouth_close_delay)