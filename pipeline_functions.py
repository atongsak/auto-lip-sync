from pydub import AudioSegment
import viseme_sets


def normalize_token(token: str) -> list[str]:
    if not token:
        return []

    token = token.strip()

    # Syllabic consonants → base consonant
    if token in ["n̩", "l̩", "m̩"]:
        return [token[0]]

    # Rare combined tokens
    if token == "əl":
        return ["ə", "l"]

    # Split vowel+r if combined
    if token.endswith("ɹ") and len(token) > 1:
        return [token[:-1], "ɹ"]

    return [token]


def cleanup_visemes(visemes, audio_end):
    if not visemes:
        return []

    cleaned = [visemes[0]]

    for curr in visemes[1:]:
        prev = cleaned[-1]

        # Gap → extend previous
        if curr["start"] > prev["end"]:
            prev["end"] = curr["start"]

        # Overlap → trim previous
        elif curr["start"] < prev["end"]:
            prev["end"] = curr["start"]

    cleaned.append(curr)

    # Prepend silence if needed
    if cleaned[0]["start"] > 0.0:
        cleaned.insert(0, {
            "token": "sil",
            "viseme": viseme_sets.MICROSOFT_22_MAPPING["sil"],  # or explicit sil
            "start": 0.0,
            "end": cleaned[0]["start"]
        })

    # Extend final viseme
    cleaned[-1]["end"] = audio_end

    return cleaned


def phonemes_to_visemes(phoneme_timings, viseme_mapping, audio_end):
    results = []

    for p in phoneme_timings:
        raw_token = p["char"]
        start = p["start"]
        end = p["end"]

        tokens = normalize_token(raw_token)

        for token in tokens:
            # --- Silence handling ---
            if token == " ":
                if start is None or end is None:
                    continue

                duration = end - start

                # Short pause → blend into previous viseme
                if results and duration < 0.4:
                    results[-1]["end"] = end
                    continue

                viseme = viseme_mapping.get("sil")

            # --- Length marker ---
            elif token == "ː":
                if results:
                    results[-1]["end"] = end
                continue

            # --- Normal phoneme ---
            else:
                viseme = viseme_mapping.get(token)

                if viseme is None:
                    # Debug but don't crash pipeline
                    print(f"No viseme for: {token}")
                    continue

            results.append({
            "token": token,
            "viseme": viseme,
            "start": start,
            "end": end
            })

    return cleanup_visemes(results, audio_end)


def get_duration_pydub(file_path):
    audio = AudioSegment.from_file(file_path)
    # Duration is returned in milliseconds, convert to seconds
    duration_seconds = len(audio) / 1000.0
    return duration_seconds