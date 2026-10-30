
"""RayX English Grammar Curriculum
Offline, rule-based grammar reference.
No external AI API. Does not modify model checkpoints.
"""

import re

CURRICULUM = {
    "parts of speech": {
        "definition": "Words are classified by the roles they perform in a sentence.",
        "topics": {
            "noun": "Names a person, place, thing, substance, or idea.",
            "pronoun": "Replaces or refers to a noun or noun phrase.",
            "verb": "Expresses an action, event, or state.",
            "adjective": "Modifies a noun or pronoun.",
            "adverb": "Modifies a verb, adjective, another adverb, or a clause.",
            "preposition": "Expresses relationships involving time, place, direction, or other relations.",
            "conjunction": "Connects words, phrases, clauses, or sentences.",
            "interjection": "Expresses a reaction or emotion.",
            "determiner": "Specifies or limits a noun, as in this, some, each, and the.",
            "article": "A, an, and the are articles used with nouns.",
        },
    },
    "noun": {
        "definition": "A noun names a person, place, thing, substance, or idea.",
        "topics": {
            "proper noun": "Names a specific person, place, organisation, or title.",
            "common noun": "Names a general class of people, places, or things.",
            "collective noun": "Refers to a group considered as a unit.",
            "abstract noun": "Names an idea, quality, state, or feeling.",
            "material noun": "Names a substance or material.",
            "countable noun": "Can normally be counted as individual units.",
            "uncountable noun": "Is not normally counted as separate units.",
            "singular and plural": "Nouns may refer to one or more than one; plural forms include regular and irregular patterns.",
            "possessive noun": "Shows possession or association, often using apostrophe-s.",
        },
    },
    "pronoun": {
        "definition": "A pronoun refers to a person or thing without repeating its noun phrase.",
        "topics": {
            "personal pronoun": "I, me, you, he, him, she, her, it, we, us, they, them.",
            "possessive pronoun": "Mine, yours, his, hers, ours, theirs.",
            "reflexive pronoun": "Myself, yourself, himself, herself, itself, ourselves, yourselves, themselves.",
            "demonstrative pronoun": "This, that, these, those.",
            "relative pronoun": "Who, whom, whose, which, that.",
            "interrogative pronoun": "Who, whom, whose, what, which when used to ask questions.",
            "indefinite pronoun": "Someone, anyone, everybody, few, several, and others.",
            "reciprocal pronoun": "Each other and one another.",
            "pronoun agreement": "Pronouns should agree with their antecedents in meaning and appropriate grammatical form.",
        },
    },
    "verb": {
        "definition": "A verb expresses an action, event, or state and forms the core of a clause.",
        "topics": {
            "main verb": "Carries the main lexical meaning.",
            "auxiliary verb": "Helps form tense, aspect, voice, questions, or negatives.",
            "modal verb": "Expresses ability, possibility, permission, obligation, or similar meanings.",
            "transitive verb": "Takes a direct object in the relevant use.",
            "intransitive verb": "Does not take a direct object in the relevant use.",
            "linking verb": "Links a subject to a subject complement.",
            "finite verb": "Shows grammatical tense or agreement in a clause.",
            "non-finite verb": "Includes infinitives, gerunds, and participles.",
            "gerund": "An -ing verb form used in a noun-like role.",
            "infinitive": "The base form, often with to, used in infinitive constructions.",
            "participle": "A verb form used in perfect and passive constructions or adjectivally.",
            "phrasal verb": "A verb combined with a particle, sometimes creating an idiomatic meaning.",
        },
    },
    "adjective and adverb": {
        "definition": "Adjectives typically modify nouns; adverbs modify verbs, adjectives, adverbs, or clauses.",
        "topics": {
            "adjective order": "Multiple adjectives often follow conventional ordering patterns, though emphasis and context can change the order.",
            "comparative adjectives": "Compare two entities, often with -er or more.",
            "superlative adjectives": "Express the highest or lowest degree in a group, often with -est or most.",
            "adverbs of frequency": "Often, usually, sometimes, rarely, never.",
            "adverbs of manner": "Describe how an action occurs.",
            "adverbs of degree": "Very, quite, too, almost, extremely.",
            "adjective or adverb": "Choose the form that matches the grammatical role, not simply the word ending.",
        },
    },
    "articles and determiners": {
        "definition": "Articles and determiners help specify which entity or how much of something is meant.",
        "topics": {
            "a and an": "Use a or an with many singular countable nouns when the referent is not specifically identified. Choose by sound, not spelling.",
            "the": "Use the when the listener can identify the referent or when context makes it specific.",
            "zero article": "Plural and uncountable nouns may take no article for general meanings.",
            "some and any": "Commonly used for quantities; their distribution depends on sentence type and meaning.",
            "much and many": "Much commonly modifies uncountable nouns; many commonly modifies plural countable nouns.",
            "few and little": "Few relates to countable nouns; little relates to uncountable nouns. A changes the meaning.",
            "each and every": "Both refer to individual members; their grammatical patterns differ.",
            "this that these those": "Demonstratives distinguish number and distance or discourse reference.",
            "possessive determiners": "My, your, his, her, its, our, their specify relationships to a noun.",
        },
    },
    "prepositions": {
        "definition": "Prepositions express relations such as location, time, direction, cause, and means.",
        "topics": {
            "in on at place": "In often marks an enclosed area, on a surface, and at a point or location; usage depends on context.",
            "in on at time": "In commonly refers to longer periods, on to days and dates, and at to specific clock times.",
            "direction prepositions": "To, into, onto, through, across, towards and other forms express different paths or endpoints.",
            "prepositional phrases": "A preposition and its complement form a phrase that functions within a larger sentence.",
            "dependent prepositions": "Some words conventionally take particular prepositions, such as interested in.",
        },
    },
    "conjunctions and clauses": {
        "definition": "Conjunctions connect units; clauses contain a subject and a predicate, with finite or non-finite structures.",
        "topics": {
            "coordinating conjunctions": "And, but, or, nor, for, so, yet can connect grammatically related units.",
            "subordinating conjunctions": "Because, although, if, when, while, unless and others introduce subordinate clauses.",
            "noun clause": "A clause that functions in a noun-like role.",
            "relative clause": "A clause that modifies a noun or identifies its referent.",
            "adverbial clause": "A clause expressing relations such as time, reason, condition, or contrast.",
            "defining relative clause": "Provides information needed to identify the noun's referent.",
            "non-defining relative clause": "Adds supplementary information and is usually separated by commas.",
        },
    },
    "sentence structure": {
        "definition": "A sentence organises words and clauses to express a complete communicative idea.",
        "topics": {
            "subject and predicate": "The subject is what a clause is about grammatically; the predicate says something about it.",
            "direct and indirect object": "A direct object is the entity affected; an indirect object often identifies a recipient or beneficiary.",
            "subject complement": "A word or phrase that describes or identifies the subject after a linking verb.",
            "object complement": "A word or phrase that describes or identifies an object.",
            "simple sentence": "Contains one independent clause.",
            "compound sentence": "Contains two or more independent clauses.",
            "complex sentence": "Contains an independent clause and at least one subordinate clause.",
            "compound complex sentence": "Contains at least two independent clauses and at least one subordinate clause.",
            "word order": "English statements commonly use subject-verb-object order, but other patterns occur for grammatical and discourse reasons.",
            "sentence fragments": "A fragment is an incomplete sentence used where a complete sentence is required.",
            "run-on sentences": "Independent clauses must be joined or punctuated appropriately, not simply run together.",
        },
    },
    "present simple": {
        "definition": "Used for habits, general truths, regular events, and certain schedules.",
        "affirmative": "Subject + base verb; add -s or -es with he, she, it and singular third-person subjects.",
        "negative": "Subject + do/does + not + base verb.",
        "question": "Do/Does + subject + base verb?",
        "examples": ["I study.", "She studies.", "They do not study.", "Does he study?"],
        "common_errors": ["She do not study. -> She does not study.", "Does he studies? -> Does he study."],
    },
    "present continuous": {
        "definition": "Used for actions in progress around now and certain temporary or arranged situations.",
        "affirmative": "Subject + am/is/are + verb-ing.",
        "negative": "Subject + am/is/are + not + verb-ing.",
        "question": "Am/Is/Are + subject + verb-ing?",
        "examples": ["I am reading.", "She is reading.", "Are they reading?"],
        "common_errors": ["She is read. -> She is reading."],
    },
    "present perfect": {
        "definition": "Connects a past event or situation to the present, often through result, experience, or duration.",
        "affirmative": "Subject + has/have + past participle.",
        "negative": "Subject + has/have + not + past participle.",
        "question": "Has/Have + subject + past participle?",
        "examples": ["I have finished.", "She has arrived.", "Have you eaten?"],
        "common_errors": ["She have finished. -> She has finished."],
    },
    "present perfect continuous": {
        "definition": "Emphasises an activity continuing over a period up to the present or its recent effects.",
        "affirmative": "Subject + has/have + been + verb-ing.",
        "negative": "Subject + has/have + not + been + verb-ing.",
        "question": "Has/Have + subject + been + verb-ing?",
        "examples": ["I have been studying for two hours.", "It has been raining."],
    },
    "past simple": {
        "definition": "Used for completed past events and past states.",
        "affirmative": "Subject + past form of the verb.",
        "negative": "Subject + did not + base verb.",
        "question": "Did + subject + base verb?",
        "examples": ["She went home.", "They did not go.", "Did you see it?"],
        "common_errors": ["Did she went? -> Did she go?"],
    },
    "past continuous": {
        "definition": "Describes an action in progress at a past time, often as background to another event.",
        "affirmative": "Subject + was/were + verb-ing.",
        "negative": "Subject + was/were + not + verb-ing.",
        "question": "Was/Were + subject + verb-ing?",
        "examples": ["I was sleeping.", "They were working.", "Were you waiting?"],
    },
    "past perfect": {
        "definition": "Marks a past event as earlier than another past reference point.",
        "affirmative": "Subject + had + past participle.",
        "negative": "Subject + had not + past participle.",
        "question": "Had + subject + past participle?",
        "examples": ["She had left before I arrived.", "Had they finished?"],
    },
    "past perfect continuous": {
        "definition": "Emphasises the duration or ongoing nature of an activity before a past reference point.",
        "affirmative": "Subject + had been + verb-ing.",
        "negative": "Subject + had not been + verb-ing.",
        "question": "Had + subject + been + verb-ing?",
        "examples": ["I had been studying before dinner.", "They had been waiting for an hour."],
    },
    "future simple": {
        "definition": "Will often expresses predictions, decisions, promises, and future statements.",
        "affirmative": "Subject + will + base verb.",
        "negative": "Subject + will not + base verb.",
        "question": "Will + subject + base verb?",
        "examples": ["I will help.", "She will not leave.", "Will they come?"],
    },
    "future continuous": {
        "definition": "Describes an action that will be in progress at a future time.",
        "affirmative": "Subject + will be + verb-ing.",
        "negative": "Subject + will not be + verb-ing.",
        "question": "Will + subject + be + verb-ing?",
        "examples": ["I will be studying at eight.", "Will you be working?"],
    },
    "future perfect": {
        "definition": "Describes an event completed by a specified future reference point.",
        "affirmative": "Subject + will have + past participle.",
        "negative": "Subject + will not have + past participle.",
        "question": "Will + subject + have + past participle?",
        "examples": ["I will have finished by Friday.", "Will she have arrived by then?"],
    },
    "future perfect continuous": {
        "definition": "Emphasises the duration of an activity up to a future reference point.",
        "affirmative": "Subject + will have been + verb-ing.",
        "negative": "Subject + will not have been + verb-ing.",
        "question": "Will + subject + have been + verb-ing?",
        "examples": ["By June, I will have been working here for a year."],
    },
    "subject verb agreement": {
        "definition": "The verb form should match its subject according to person, number, and construction.",
        "topics": {
            "third person singular": "In the present simple, singular third-person subjects usually take a verb ending in -s or -es.",
            "compound subjects": "Subjects joined by and usually take a plural verb, with meaning and fixed expressions affecting some cases.",
            "each and every agreement": "Each and every commonly take a singular verb when they are the subject.",
            "collective noun agreement": "Collective nouns may take singular or plural agreement depending on dialect and whether the group is treated as a unit or individuals.",
            "there is and there are": "The verb agrees with the notional subject that follows in standard constructions.",
        },
    },
    "modal verbs": {
        "definition": "Modals express meanings such as ability, possibility, permission, advice, prediction, and obligation.",
        "topics": {
            "can and could": "Often express ability or possibility; could also has polite and conditional uses.",
            "may and might": "Often express possibility or permission, depending on context.",
            "must": "Can express strong obligation or a confident inference.",
            "should and ought to": "Often express advice, expectation, or what is appropriate.",
            "have to": "Often expresses obligation or necessity.",
            "would": "Appears in polite requests, hypothetical situations, habits in the past, and reported speech.",
            "modal structure": "A central modal is followed by a base-form verb without to, except in structures such as ought to.",
        },
    },
    "active and passive voice": {
        "definition": "Active voice presents the subject as performing the action; passive voice presents the affected entity as the subject.",
        "active_pattern": "Subject + verb + object.",
        "passive_pattern": "Object + appropriate form of be + past participle (+ by + agent).",
        "rules": [
            "Only verbs that allow an object generally form ordinary passives.",
            "Keep the tense and aspect consistent when changing voice.",
            "The agent can be omitted when unknown, obvious, or unimportant.",
            "Modal passive: modal + be + past participle.",
        ],
        "examples": ["Active: The chef cooked the meal.", "Passive: The meal was cooked by the chef."],
    },
    "direct and indirect speech": {
        "definition": "Direct speech quotes the original words; indirect or reported speech conveys the meaning without quoting them exactly.",
        "rules": [
            "Pronouns and time/place expressions may change with the reporting context.",
            "When the reporting verb is in the past, backshift often occurs, but not every sentence requires it.",
            "Reported yes/no questions commonly use if or whether and statement word order.",
            "Reported wh-questions retain the question word but use statement word order.",
            "Reported commands and requests commonly use tell, ask, or similar verbs + object + to-infinitive.",
        ],
        "examples": [
            'Direct: She said, "I am tired."',
            "Reported: She said that she was tired.",
            'Direct: He asked, "Are you ready?"',
            "Reported: He asked whether I was ready.",
        ],
    },
    "conditionals": {
        "definition": "Conditional constructions express conditions and their results; their forms depend on meaning and context.",
        "topics": {
            "zero conditional": "If + present simple, present simple; commonly used for general truths and regular results.",
            "first conditional": "If + present form, will + base verb is a common pattern for real future possibilities.",
            "second conditional": "If + past form, would + base verb commonly describes hypothetical or unlikely situations.",
            "third conditional": "If + past perfect, would have + past participle commonly describes unreal past situations.",
            "mixed conditional": "Combines past and present time references when the condition and result refer to different times.",
            "unless": "Often means if not, but it cannot replace if not in every context.",
        },
    },
    "questions and negatives": {
        "definition": "English questions and negatives commonly use auxiliaries and particular word orders.",
        "topics": {
            "yes no questions": "Place an auxiliary or modal before the subject in ordinary questions.",
            "wh questions": "Use who, what, where, when, why, which, or how; word order depends on whether the question word is the subject.",
            "do support": "Use do, does, or did when needed for ordinary present or past simple questions and negatives.",
            "question tags": "Short tags commonly use an auxiliary and a pronoun; polarity and intonation affect meaning.",
            "negative forms": "Not usually follows an auxiliary or modal; do-support is used when there is no suitable auxiliary.",
            "indirect questions": "Use statement word order after phrases such as Could you tell me where...?",
        },
    },
    "common grammar errors": {
        "definition": "Recognise frequent errors while remembering that acceptable usage can vary by context and dialect.",
        "corrections": {
            "She go to school.": "She goes to school.",
            "He don't know.": "He doesn't know.",
            "Did you went there?": "Did you go there?",
            "I have saw it.": "I have seen it.",
            "She is more taller.": "She is taller.",
            "An university": "A university (the word begins with a /y/ consonant sound).",
            "He is good in English.": "He is good at English. (Common standard collocation.)",
            "I am agree.": "I agree.",
            "Discuss about the topic.": "Discuss the topic.",
            "One of my friend": "One of my friends.",
        },
    },
    "punctuation and capitalization": {
        "definition": "Punctuation marks sentence boundaries and relationships; capitalization follows standard writing conventions.",
        "topics": {
            "full stop": "Marks the end of many declarative sentences.",
            "comma": "Separates items and marks certain introductory, parenthetical, or clause boundaries; avoid comma splices.",
            "semicolon": "Can connect closely related independent clauses or separate complex list items.",
            "colon": "Can introduce an explanation, list, or elaboration after a suitable clause.",
            "apostrophe": "Marks possession and contractions; it does not normally form ordinary plurals.",
            "quotation marks": "Mark direct quotations in styles that use them.",
            "capital letters": "Capitalize sentence beginnings, the pronoun I, and proper names in standard English.",
        },
    },
    "sentence transformation": {
        "definition": "Rephrase a sentence while preserving the intended meaning and grammatical relationships.",
        "topics": {
            "affirmative and negative": "Transform polarity carefully; not every negative sentence has an equivalent with identical nuance.",
            "simple compound complex": "Change clause structure while preserving meaning as far as possible.",
            "degrees of comparison": "Use positive, comparative, and superlative structures appropriately.",
            "too and enough": "Too commonly signals excess; enough signals sufficiency and has position rules.",
            "so and such": "So commonly modifies adjectives/adverbs; such commonly modifies noun phrases.",
            "although and despite": "Although takes a clause; despite normally takes a noun phrase or gerund.",
        },
    },
}

ALIASES = {
    "tenses": "present simple",
    "present tense": "present simple",
    "past tense": "past simple",
    "future tense": "future simple",
    "voice": "active and passive voice",
    "passive voice": "active and passive voice",
    "reported speech": "direct and indirect speech",
    "indirect speech": "direct and indirect speech",
    "parts of speech": "parts of speech",
    "sentence": "sentence structure",
    "conditionals": "conditionals",
    "articles": "articles and determiners",
    "preposition": "prepositions",
    "conjunction": "conjunctions and clauses",
    "agreement": "subject verb agreement",
    "modal": "modal verbs",
    "punctuation": "punctuation and capitalization",
    "error correction": "common grammar errors",
    "grammar mistakes": "common grammar errors",
    "transformations": "sentence transformation",
}


def normalize(text):
    text = str(text).casefold().strip()
    text = re.sub(r"[^\w\s'-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def all_topics():
    result = set(CURRICULUM)
    for section in CURRICULUM.values():
        result.update(section.get("topics", {}))
    result.update(ALIASES)
    return sorted(result)


def find_topic(question):
    normalized = normalize(question)
    candidates = sorted(all_topics(), key=len, reverse=True)

    for candidate in candidates:
        pattern = r"(?<!\w)" + re.escape(candidate) + r"(?!\w)"
        if re.search(pattern, normalized):
            return ALIASES.get(candidate, candidate)

    return None


def format_section(title, section):
    lines = [title.title()]

    for key in ("definition", "affirmative", "negative", "question",
                "active_pattern", "passive_pattern"):
        if key in section:
            lines.append(f"\n{key.replace('_', ' ').title()}: {section[key]}")

    for key in ("topics", "rules", "examples", "common_errors", "corrections"):
        value = section.get(key)
        if not value:
            continue

        lines.append(f"\n{key.replace('_', ' ').title()}:")

        if isinstance(value, dict):
            for name, explanation in value.items():
                lines.append(f"- {name}: {explanation}")
        else:
            for item in value:
                lines.append(f"- {item}")

    return "\n".join(lines)


def answer_grammar_question(question):
    normalized = normalize(question)

    if any(phrase in normalized for phrase in (
        "complete grammar", "full grammar", "all grammar",
        "entire grammar", "english grammar syllabus",
        "teach me english grammar", "learn english grammar",
    )):
        titles = "\n".join(
            f"- {name.title()}" for name in CURRICULUM
        )
        return {
            "answer": (
                "RayX English Grammar Curriculum\n\n"
                "The curriculum covers these major areas:\n"
                f"{titles}\n\n"
                "Ask for any topic by name to open its lesson. "
                "This is a structured reference, not yet an unrestricted "
                "grammar parser or a complete textbook."
            ),
            "topic": "overview",
            "verified": True,
        }

    # Show the correction list when explicitly requested.
    if any(phrase in normalized for phrase in (
        "common grammar errors", "common mistakes",
        "error correction", "grammar mistakes",
    )):
        section = CURRICULUM["common grammar errors"]
        return {
            "answer": format_section("Common Grammar Errors", section),
            "topic": "common grammar errors",
            "verified": True,
        }

    topic = find_topic(normalized)
    if not topic:
        return None

    # Exact top-level section or a recognized subtopic.
    if topic in CURRICULUM:
        section = CURRICULUM[topic]
        answer = format_section(topic, section)
    else:
        answer = None
        for section_name, section in CURRICULUM.items():
            if topic in section.get("topics", {}):
                answer = (
                    f"{topic.title()}\n\n"
                    f"{section['topics'][topic]}"
                )
                break

        if answer is None:
            return None

    return {
        "answer": answer,
        "topic": topic,
        "verified": True,
    }

    
def correct_english_sentence(sentence):
    """Correct a few known sentence patterns using explicit rules."""
    text = str(sentence).strip()
    normalized = normalize(text)

    # Example: i name is rajan -> My name is Rajan.
    match = re.fullmatch(
        r"i\s+name\s+is\s+([a-z][a-z'-]*)[.!?]*",
        normalized,
    )
    if match:
        name = match.group(1)
        name = name[0].upper() + name[1:]
        return {
            "answer": (
                f"Correct sentence: My name is {name}.\n\n"
                "Rule: Use 'My name is ...' to introduce your name. "
                "Capitalize the pronoun 'I' and people's names."
            ),
            "topic": "sentence correction",
            "verified": True,
        }

    # Example: i are 10 apple -> intent is ambiguous.
    match = re.fullmatch(
        r"i\s+are\s+(\d+)\s+apples?",
        normalized,
    )
    if match:
        number = match.group(1)
        return {
            "answer": (
                "Your sentence needs correction. The intended meaning "
                "is not completely clear.\n\n"
                f"1. If you mean possession: I have {number} apples.\n"
                f"2. If you mean age: I am {number} years old.\n\n"
                "Rules:\n"
                "- Use 'have' to express possession.\n"
                "- Use 'am' with 'I', not 'are'.\n"
                "- Use a plural noun after numbers greater than one."
            ),
            "topic": "sentence correction",
            "verified": True,
        }

    return None



if __name__ == "__main__":
    for question in (
        "Teach me complete English grammar",
        "Explain all 12 tenses",
        "Explain present perfect",
        "Explain passive voice",
        "Show common grammar errors",
        "Explain conditionals",
    ):
        result = answer_grammar_question(question)
        print("\n" + "=" * 60)
        print("Question:", question)
        print(result["answer"] if result else "Topic not found")
