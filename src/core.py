import time
import threading
import concurrent.futures
import json
import os
from typing import List, Dict, Any, Optional
from model_adapter import ModelAdapter, get_model_adapter

def display_progress_bar(iteration, total, prefix='', suffix='', length=50, fill='█', success=0, failed=0):
    """显示进度条"""
    percent = 100 * (iteration / float(total))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    status = f"{success}成功, {failed}失败" if (success + failed) > 0 else ""
    print(f'\r{prefix} |{bar}| {percent:.1f}% {suffix} {status}', end='\r')
    if iteration == total:
        print()

# 加载 tokenizer 词汇表
VOCAB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'vocab.json')

def load_vocab():
    """加载 vocab.json 文件并返回有意义的单词列表"""
    try:
        with open(VOCAB_PATH, 'r', encoding='utf-8') as f:
            vocab = json.load(f)
        
        # 过滤出有意义的单词（纯英文单词）
        meaningful_words = []
        for token in vocab.keys():
            # 只保留纯英文单词（只包含字母）
            # 排除特殊字符、单个字符、数字等
            if token.isalpha() and len(token) > 1:
                # 只保留ASCII字符范围内的英文单词
                if all(ord(c) < 128 for c in token):
                    meaningful_words.append(token)
        
        return meaningful_words
    except FileNotFoundError:
        print(f"警告: 未找到词汇表文件 {VOCAB_PATH}，使用内置词汇表")
        return []

# 尝试加载词汇表
TOKEN_VOCABULARY = load_vocab()
VOCAB_SIZE = len(TOKEN_VOCABULARY)

# 如果加载失败，使用扩展词汇表作为备选
if VOCAB_SIZE == 0:
    EXTENDED_VOCABULARY = [
    # 基础词汇
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it", "for", "not", "on", "with", "he",
    "as", "you", "do", "at", "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
    "or", "an", "will", "my", "one", "all", "would", "there", "their", "what", "so", "up", "out", "if",
    "about", "who", "get", "which", "go", "me", "when", "make", "can", "like", "time", "no", "just",
    "him", "know", "take", "people", "into", "year", "your", "good", "some", "could", "them", "see",
    "other", "than", "then", "now", "look", "only", "come", "its", "over", "think", "also", "back",
    "after", "use", "two", "how", "our", "work", "first", "well", "way", "even", "new", "want",
    "because", "any", "these", "give", "day", "most", "us",
    # 扩展词汇
    "is", "was", "are", "were", "been", "has", "had", "did", "does", "doing", "done", "being",
    "am", "were", "was", "been", "being", "have", "has", "had", "do", "does", "did", "doing",
    "the", "a", "an", "this", "that", "these", "those", "my", "your", "his", "her", "its",
    "our", "their", "what", "which", "who", "whom", "whose", "whatever", "whichever", "whoever",
    "whomever", "and", "but", "or", "yet", "so", "for", "nor", "either", "neither", "both",
    "whether", "if", "unless", "though", "although", "while", "whereas", "because", "since",
    "as", "before", "after", "until", "till", "when", "whenever", "where", "wherever", "than",
    "once", "whenever", "how", "however", "why", "what", "whatever", "which", "whichever",
    "who", "whoever", "whom", "whomever", "whose", "of", "in", "to", "for", "with", "on",
    "at", "from", "by", "about", "into", "through", "during", "before", "after", "above",
    "below", "between", "among", "within", "without", "against", "under", "over", "behind",
    "beyond", "across", "around", "near", "off", "past", "toward", "towards", "upon",
    "very", "really", "quite", "rather", "pretty", "fairly", "extremely", "incredibly",
    "absolutely", "completely", "totally", "entirely", "fully", "highly", "greatly",
    "deeply", "strongly", "widely", "clearly", "obviously", "certainly", "definitely",
    "probably", "possibly", "perhaps", "maybe", "likely", "unlikely", "actually",
    "really", "truly", "literally", "seriously", "honestly", "basically", "essentially",
    "generally", "usually", "normally", "typically", "commonly", "frequently", "often",
    "sometimes", "occasionally", "rarely", "seldom", "never", "always", "constantly",
    "continuously", "repeatedly", "regularly", "daily", "weekly", "monthly", "yearly",
    "here", "there", "where", "everywhere", "somewhere", "anywhere", "nowhere", "elsewhere",
    "home", "away", "abroad", "overseas", "indoors", "outdoors", "upstairs", "downstairs",
    "up", "down", "left", "right", "forward", "backward", "ahead", "behind", "beside",
    "above", "below", "under", "over", "inside", "outside", "within", "without",
    "man", "woman", "child", "children", "person", "people", "family", "friend", "group",
    "team", "company", "government", "school", "university", "college", "student",
    "teacher", "doctor", "worker", "player", "member", "leader", "manager", "customer",
    "user", "client", "patient", "guest", "visitor", "driver", "artist", "author",
    "scientist", "engineer", "lawyer", "police", "soldier", "farmer", "cook", "waiter",
    "actor", "singer", "dancer", "writer", "reader", "listener", "viewer", "buyer",
    "seller", "owner", "partner", "neighbor", "stranger", "enemy", "hero", "victim",
    "animal", "dog", "cat", "bird", "fish", "horse", "cow", "pig", "sheep", "chicken",
    "lion", "tiger", "bear", "wolf", "fox", "deer", "rabbit", "mouse", "rat", "snake",
    "tree", "flower", "grass", "plant", "forest", "mountain", "river", "lake", "ocean",
    "sea", "beach", "island", "desert", "valley", "hill", "rock", "stone", "sand",
    "water", "rain", "snow", "ice", "wind", "cloud", "sky", "sun", "moon", "star",
    "earth", "world", "land", "ground", "soil", "field", "farm", "garden", "park",
    "city", "town", "village", "country", "nation", "state", "capital", "building",
    "house", "home", "room", "kitchen", "bedroom", "bathroom", "living", "office",
    "store", "shop", "market", "restaurant", "hotel", "hospital", "church", "temple",
    "road", "street", "way", "path", "bridge", "tunnel", "wall", "door", "window",
    "roof", "floor", "ceiling", "stairs", "elevator", "car", "bus", "train", "plane",
    "ship", "boat", "bike", "truck", "computer", "phone", "screen", "keyboard",
    "mouse", "camera", "television", "radio", "music", "song", "movie", "book",
    "paper", "pen", "pencil", "letter", "word", "sentence", "page", "story", "news",
    "information", "data", "knowledge", "idea", "thought", "opinion", "view", "fact",
    "truth", "lie", "joke", "question", "answer", "problem", "solution", "result",
    "effect", "cause", "reason", "purpose", "goal", "aim", "plan", "strategy",
    "method", "way", "approach", "process", "system", "structure", "organization",
    "program", "project", "task", "job", "work", "career", "business", "industry",
    "market", "economy", "money", "dollar", "price", "cost", "value", "worth",
    "amount", "number", "quantity", "quality", "level", "degree", "rate", "speed",
    "size", "shape", "color", "red", "blue", "green", "yellow", "white", "black",
    "big", "small", "large", "little", "tiny", "huge", "long", "short", "tall",
    "high", "low", "wide", "narrow", "deep", "shallow", "thick", "thin", "heavy",
    "light", "strong", "weak", "hard", "soft", "smooth", "rough", "sharp", "dull",
    "clean", "dirty", "wet", "dry", "hot", "cold", "warm", "cool", "fresh", "stale",
    "new", "old", "young", "ancient", "modern", "current", "present", "past", "future",
    "early", "late", "soon", "now", "today", "tomorrow", "yesterday", "morning",
    "afternoon", "evening", "night", "day", "week", "month", "year", "century",
    "time", "moment", "minute", "hour", "second", "period", "era", "age", "date",
    "happy", "sad", "angry", "afraid", "worried", "excited", "bored", "tired",
    "surprised", "shocked", "pleased", "satisfied", "disappointed", "proud", "ashamed",
    "jealous", "grateful", "sorry", "guilty", "innocent", "confident", "nervous",
    "calm", "relaxed", "stressed", "anxious", "depressed", "optimistic", "pessimistic",
    "good", "bad", "better", "best", "worse", "worst", "great", "excellent",
    "wonderful", "amazing", "fantastic", "terrible", "awful", "horrible", "nice",
    "fine", "okay", "perfect", "beautiful", "ugly", "pretty", "handsome", "attractive",
    "interesting", "boring", "fun", "funny", "serious", "important", "necessary",
    "possible", "impossible", "easy", "difficult", "hard", "simple", "complex",
    "complicated", "clear", "unclear", "obvious", "hidden", "secret", "private",
    "public", "open", "closed", "free", "expensive", "cheap", "rich", "poor",
    "safe", "dangerous", "risky", "secure", "protected", "vulnerable", "weak",
    "healthy", "sick", "ill", "dead", "alive", "living", "real", "fake", "true",
    "false", "right", "wrong", "correct", "incorrect", "accurate", "inaccurate",
    "exact", "precise", "specific", "general", "particular", "special", "unique",
    "common", "rare", "usual", "unusual", "normal", "abnormal", "regular", "irregular",
    "standard", "average", "normal", "typical", "different", "similar", "same",
    "opposite", "various", "several", "many", "much", "few", "little", "more",
    "less", "most", "least", "all", "none", "nothing", "everything", "anything",
    "something", "someone", "anyone", "everyone", "nobody", "everybody", "anybody",
    "somebody", "each", "every", "both", "either", "neither", "other", "another",
    "such", "only", "just", "even", "also", "too", "either", "neither", "both",
    "all", "none", "no", "not", "never", "always", "often", "usually", "sometimes",
    "rarely", "seldom", "frequently", "occasionally", "regularly", "daily", "weekly",
    "here", "there", "where", "everywhere", "somewhere", "anywhere", "nowhere",
    "elsewhere", "everyplace", "someplace", "anyplace", "noplace",
    "up", "down", "left", "right", "forward", "backward", "ahead", "behind",
    "above", "below", "over", "under", "inside", "outside", "within", "without",
    "across", "through", "into", "onto", "upon", "off", "away", "apart", "together",
    "fast", "slow", "quick", "rapid", "swift", "speedy", "gradual", "sudden",
    "immediately", "instantly", "quickly", "slowly", "gradually", "suddenly",
    "finally", "eventually", "initially", "originally", "previously", "formerly",
    "recently", "lately", "currently", "presently", "simultaneously", "meanwhile",
    "first", "second", "third", "last", "final", "next", "previous", "following",
    "subsequent", "prior", "earlier", "later", "before", "after", "during", "while",
    "meantime", "throughout", "through", "across", "along", "around", "about",
    "regarding", "concerning", "respecting", "touching", "involving", "including",
    "excluding", "except", "besides", "beyond", "beside", "near", "close", "distant",
    "far", "away", "apart", "together", "alone", "single", "double", "triple",
    "multiple", "various", "diverse", "different", "distinct", "separate", "individual",
    "personal", "private", "public", "collective", "shared", "joint", "mutual",
    "reciprocal", "common", "universal", "general", "widespread", "prevalent",
    "popular", "famous", "well-known", "unknown", "obscure", "hidden", "secret",
    "mysterious", "strange", "weird", "odd", "peculiar", "unusual", "extraordinary",
    "remarkable", "outstanding", "exceptional", "excellent", "superb", "magnificent",
    "splendid", "grand", "impressive", "striking", "stunning", "amazing", "astonishing",
    "astounding", "surprising", "shocking", "startling", "disturbing", "troubling",
    "worrying", "concerning", "alarming", "frightening", "scary", "terrifying",
    "horrifying", "disgusting", "revolting", "repulsive", "offensive", "unpleasant",
    "disagreeable", "nasty", "awful", "terrible", "horrible", "dreadful",
    "appalling", "atrocious", "abominable", "deplorable", "lamentable", "regrettable",
    "unfortunate", "unlucky", "disastrous", "catastrophic", "tragic", "fatal",
    "deadly", "mortal", "lethal", "toxic", "poisonous", "harmful", "damaging",
    "destructive", "ruinous", "devastating", "damaging", "injurious", "hurtful",
    "painful", "uncomfortable", "distressing", "upsetting", "disturbing", "troubling",
    "bothersome", "annoying", "irritating", "frustrating", "aggravating", "exasperating",
    "infuriating", "maddening", "rage-inducing", "anger-provoking", "provocative",
    "challenging", "demanding", "difficult", "hard", "tough", "rough", "rugged",
    "strenuous", "arduous", "laborious", "toilsome", "onerous", "burdensome",
    "heavy", "weighty", "substantial", "considerable", "significant", "important",
    "major", "main", "primary", "principal", "chief", "key", "central", "crucial",
    "critical", "essential", "vital", "necessary", "needed", "required", "mandatory",
    "obligatory", "compulsory", "forced", "involuntary", "unwilling", "reluctant",
    "hesitant", "uncertain", "unsure", "doubtful", "dubious", "skeptical",
    "suspicious", "mistrustful", "distrustful", "wary", "cautious", "careful",
    "prudent", "sensible", "reasonable", "rational", "logical", "sane", "sound",
    "valid", "legitimate", "lawful", "legal", "licit", "permissible", "allowable",
    "acceptable", "tolerable", "bearable", "endurable", "sufferable", "supportable",
    "sustainable", "maintainable", "manageable", "controllable", "governable",
    "rulable", "regulable", "adjustable", "adaptable", "flexible", "pliant",
    "pliant", "compliant", "obedient", "submissive", "docile", "meek", "mild",
    "gentle", "tender", "soft", "kind", "kindly", "benevolent", "benign",
    "beneficent", "charitable", "altruistic", "humanitarian", "philanthropic",
    "generous", "liberal", "magnanimous", "unselfish", "selfless", "considerate",
    "thoughtful", "attentive", "mindful", "heedful", "careful", "cautious",
    "prudent", "discreet", "circumspect", "wary", "guarded", "vigilant", "watchful",
    "alert", "aware", "conscious", "cognizant", "mindful", "sensible", "sensitive",
    "perceptive", "observant", "discerning", "discriminating", "discriminative",
    "distinctive", "characteristic", "typical", "representative", "symbolic",
    "emblematic", "indicative", "suggestive", "evocative", "reminiscent",
    "redolent", "fragrant", "aromatic", "odorous", "scented", "perfumed",
    "sweet-smelling", "fresh", "clean", "pure", "clear", "transparent",
    "translucent", "limpid", "crystalline", "glassy", "vitreous", "shiny",
    "glossy", "lustrous", "radiant", "brilliant", "dazzling", "blinding",
    "bright", "light", "luminous", "illuminated", "lit", "lighted", "shining",
    "glowing", "gleaming", "glistening", "glittering", "sparkling", "twinkling",
    "shimmering", "flickering", "flashing", "blinking", "winking", "fluttering",
    "flapping", "waving", "swaying", "swinging", "rocking", "rolling", "pitching",
    "tossing", "turning", "rotating", "revolving", "spinning", "whirling",
    "twirling", "swirling", "circling", "circling", "orbiting", "cycling",
    "recycling", "repeating", "reiterating", "restating", "rephrasing",
    "rewording", "reformulating", "reconstructing", "rebuilding", "reconstructing",
    "remaking", "recreating", "regenerating", "renewing", "restoring",
    "restoring", "repairing", "fixing", "mending", "patching", "healing",
    "curing", "remedying", "correcting", "rectifying", "ameliorating",
    "improving", "bettering", "enhancing", "enriching", "upgrading",
    "refining", "polishing", "perfecting", "completing", "finishing",
    "concluding", "ending", "terminating", "closing", "shutting", "sealing",
    "locking", "securing", "protecting", "guarding", "defending", "shielding",
    "sheltering", "harboring", "housing", "accommodating", "lodging",
    "quartering", "boarding", "billeting", "stationing", "posting",
    "positioning", "placing", "locating", "situating", "establishing",
    "founding", "creating", "making", "building", "constructing", "erecting",
    "raising", "lifting", "elevating", "hoisting", "heaving", "hauling",
    "pulling", "drawing", "dragging", "towing", "tugging", "yanking",
    "jerking", "twitching", "shaking", "shuddering", "shivering", "trembling",
    "quivering", "quaking", "vibrating", "oscillating", "swinging", "swaying",
    "rocking", "rolling", "pitching", "tossing", "turning", "twisting",
    "winding", "coiling", "curling", "bending", "flexing", "arching",
    "curving", "bowing", "stooping", "crouching", "squatting", "kneeling",
    "sitting", "seating", "perching", "roosting", "nesting", "settling",
    "establishing", "rooting", "grounding", "founding", "basing", "resting",
    "relying", "depending", "counting", "reckoning", "calculating",
    "computing", "figuring", "estimating", "guessing", "speculating",
    "conjecturing", "surmising", "inferring", "deducing", "concluding",
    "reasoning", "thinking", "cogitating", "pondering", "contemplating",
    "meditating", "reflecting", "musing", "ruminating", "brooding",
    "worrying", "fretting", "agonizing", "anguishing", "suffering",
    "enduring", "bearing", "withstanding", "tolerating", "abiding",
    "accepting", "receiving", "getting", "obtaining", "acquiring",
    "gaining", "earning", "winning", "achieving", "attaining",
    "reaching", "arriving", "coming", "approaching", "nearing",
    "closing", "catching", "capturing", "seizing", "grabbing",
    "snatching", "taking", "grasping", "clutching", "clinging",
    "holding", "keeping", "retaining", "maintaining", "preserving",
    "conserving", "saving", "storing", "hoarding", "accumulating",
    "amassing", "collecting", "gathering", "assembling", "congregating",
    "convening", "meeting", "encountering", "facing", "confronting",
    "opposing", "resisting", "defying", "challenging", "daring",
    "risking", "venturing", "adventuring", "exploring", "investigating",
    "examining", "inspecting", "scrutinizing", "studying", "analyzing",
    "researching", "searching", "seeking", "looking", "hunting",
    "pursuing", "chasing", "following", "tracking", "trailing",
    "shadowing", "stalking", "pursuing", "chasing", "running",
    "racing", "speeding", "hurrying", "hastening", "rushing",
    "dashing", "darting", "shooting", "flying", "soaring",
    "gliding", "sailing", "floating", "drifting", "gliding",
    "sliding", "slipping", "skidding", "slithering", "creeping",
    "crawling", "climbing", "ascending", "mounting", "rising",
    "lifting", "raising", "elevating", "hoisting", "heaving",
    "throwing", "tossing", "hurling", "flinging", "casting",
    "pitching", "lobbing", "launching", "projecting", "propelling",
    "driving", "pushing", "shoving", "thrusting", "pressing",
    "squeezing", "compressing", "condensing", "contracting",
    "shrinking", "reducing", "decreasing", "lessening", "lowering",
    "dropping", "falling", "descending", "sinking", "submerging",
    "diving", "plunging", "plummeting", "crashing", "colliding",
    "hitting", "striking", "slapping", "smacking", "punching",
    "kicking", "stomping", "trampling", "treading", "stepping",
    "walking", "marching", "parading", "striding", "strutting",
    "strolling", "sauntering", "wandering", "roaming", "rambling",
    "meandering", "roving", "ranging", "traversing", "crossing",
    "passing", "surpassing", "exceeding", "transcending", "outdoing",
    "outstripping", "eclipsing", "overshadowing", "dwarfing",
    "dominating", "controlling", "commanding", "leading", "guiding",
    "directing", "managing", "supervising", "overseeing", "monitoring",
    "watching", "observing", "viewing", "seeing", "looking",
    "gazing", "staring", "peering", "peeking", "glancing",
    "scanning", "surveying", "reviewing", "inspecting", "examining",
    "checking", "testing", "trying", "attempting", "endeavoring",
    "striving", "struggling", "laboring", "toiling", "working",
    "operating", "functioning", "running", "going", "moving",
    "acting", "behaving", "performing", "executing", "implementing",
    "enforcing", "applying", "practicing", "exercising", "training",
    "drilling", "rehearsing", "preparing", "readying", "arranging",
    "organizing", "ordering", "systematizing", "methodizing",
    "standardizing", "normalizing", "regularizing", "regulating",
    "adjusting", "adapting", "modifying", "altering", "changing",
    "varying", "diversifying", "differentiating", "distinguishing",
    "discriminating", "differentiating", "separating", "dividing",
    "splitting", "breaking", "cracking", "fracturing", "shattering",
    "smashing", "crushing", "grinding", "pounding", "beating",
    "hitting", "striking", "knocking", "tapping", "rapping",
    "patting", "touching", "feeling", "sensing", "perceiving",
    "noticing", "noting", "observing", "remark", "commenting",
    "mentioning", "referring", "alluding", "hinting", "suggesting",
    "implying", "inferring", "deducing", "concluding", "deciding",
    "determining", "resolving", "settling", "fixing", "establishing",
    "instituting", "founding", "creating", "making", "producing",
    "generating", "forming", "shaping", "molding", "modeling",
    "fashioning", "designing", "planning", "plotting", "scheming",
    "conspiring", "colluding", "cooperating", "collaborating",
    "coordinating", "synchronizing", "harmonizing", "unifying",
    "uniting", "joining", "combining", "merging", "fusing",
    "blending", "mixing", "mingling", "integrating", "incorporating",
    "including", "containing", "comprising", "consisting",
    "involving", "entailing", "necessitating", "requiring",
    "demanding", "requesting", "asking", "inquiring", "questioning",
    "querying", "interrogating", "examining", "investigating",
    "exploring", "probing", "delving", "digging", "mining",
    "excavating", "extracting", "removing", "taking", "withdrawing",
    "extracting", "deriving", "obtaining", "getting", "acquiring",
    "gaining", "procuring", "securing", "ensuring", "assuring",
    "guaranteeing", "warranting", "certifying", "verifying",
    "confirming", "validating", "authenticating", "substantiating",
    "proving", "demonstrating", "showing", "displaying", "exhibiting",
    "presenting", "offering", "proposing", "suggesting", "recommending",
    "advising", "counseling", "guiding", "directing", "instructing",
    "teaching", "educating", "training", "coaching", "tutoring",
    "schooling", "indoctrinating", "brainwashing", "conditioning",
    "programming", "coding", "encoding", "encrypting", "decrypting",
    "decoding", "interpreting", "translating", "converting",
    "transforming", "transmuting", "transfiguring", "metamorphosing",
    "evolving", "developing", "growing", "expanding", "extending",
    "stretching", "spreading", "distributing", "dispersing",
    "scattering", "disseminating", "propagating", "broadcasting",
    "transmitting", "sending", "dispatching", "shipping",
    "transporting", "conveying", "carrying", "bearing", "bringing",
    "fetching", "delivering", "handing", "giving", "donating",
    "contributing", "subscribing", "paying", "spending", "expending",
    "disbursing", "distributing", "allocating", "assigning",
    "allotting", "apportioning", "dividing", "sharing", "participating",
    "partaking", "joining", "entering", "accessing", "approaching",
    "reaching", "attaining", "achieving", "accomplishing", "fulfilling",
    "completing", "finishing", "concluding", "terminating", "ending",
    "closing", "stopping", "ceasing", "halting", "pausing",
    "breaking", "interrupting", "suspending", "delaying", "postponing",
    "deferring", "putting", "placing", "laying", "setting",
    "positioning", "locating", "situating", "installing", "establishing",
    "founding", "building", "constructing", "erecting", "raising",
    "elevating", "promoting", "advancing", "progressing", "proceeding",
    "continuing", "persisting", "persevering", "enduring", "lasting",
    "remaining", "staying", "abiding", "dwelling", "residing",
    "living", "inhabiting", "occupying", "possessing", "owning",
    "having", "holding", "keeping", "retaining", "maintaining",
    "sustaining", "supporting", "upholding", "bearing", "carrying",
    "shouldering", "shouldering", "managing", "handling", "coping",
    "dealing", "treating", "handling", "processing", "manipulating",
    "operating", "working", "functioning", "performing", "serving",
    "acting", "playing", "performing", "executing", "discharging",
    "fulfilling", "satisfying", "meeting", "serving", "suiting",
    "fitting", "matching", "corresponding", "agreeing", "accord",
    "harmonizing", "conforming", "complying", "adhering", "sticking",
    "clinging", "holding", "grasping", "gripping", "clutching",
    "seizing", "capturing", "catching", "trapping", "snaring",
    "netting", "bagging", "landing", "hooking", "hitting",
    "striking", "knocking", "bumping", "colliding", "crashing",
    "smashing", "shattering", "breaking", "cracking", "splitting",
    "tearing", "ripping", "pulling", "drawing", "dragging",
    "hauling", "towing", "tugging", "heaving", "lifting",
    "raising", "elevating", "hoisting", "boosting", "increasing",
    "augmenting", "enhancing", "intensifying", "strengthening",
    "fortifying", "reinforcing", "supporting", "backing", "aiding",
    "assisting", "helping", "abetting", "facilitating", "easing",
    "smoothing", "simplifying", "clarifying", "explaining",
    "elucidating", "illuminating", "enlightening", "informing",
    "notifying", "telling", "reporting", "announcing", "declaring",
    "stating", "asserting", "affirming", "alleging", "claiming",
    "contending", "maintaining", "insisting", "demanding", "requiring",
    "requesting", "asking", "seeking", "pursuing", "chasing",
    "following", "tracking", "hunting", "searching", "looking",
    "hoping", "wishing", "wanting", "desiring", "craving",
    "longing", "yearning", "pining", "thirsting", "hungering",
    "needing", "requiring", "lacking", "missing", "wanting"
]
    TOKEN_VOCABULARY = EXTENDED_VOCABULARY
    VOCAB_SIZE = len(TOKEN_VOCABULARY)

class ModelPerfTest:
    def __init__(self, total: int, input_tokens: int, output_tokens: int, model_adapter: Optional[ModelAdapter] = None, max_concurrency: Optional[int] = None, model_name: Optional[str] = None, ignore_eos: bool = False, rounds: int = 0, wait_rounds: bool = False, input_data_type: str = 'random', custom_data_path: Optional[str] = None, scenario: Optional[str] = None, enable_thinking: bool = False):
        self.total = total
        self.max_concurrency = max_concurrency
        # 处理输入token数范围
        if isinstance(input_tokens, tuple):
            self.input_tokens_min, self.input_tokens_max = input_tokens
        else:
            self.input_tokens_min = self.input_tokens_max = input_tokens
        # 处理输出token数范围
        if isinstance(output_tokens, tuple):
            self.output_tokens_min, self.output_tokens_max = output_tokens
        else:
            self.output_tokens_min = self.output_tokens_max = output_tokens
        self.input_tokens = input_tokens  # 保留原始值用于显示
        self.output_tokens = output_tokens  # 保留原始值用于显示
        self.ignore_eos = ignore_eos
        self.rounds = rounds
        self.wait_rounds = wait_rounds
        self.input_data_type = input_data_type
        self.custom_data_path = custom_data_path
        self.scenario = scenario
        self.enable_thinking = enable_thinking
        self.model_adapter = model_adapter or get_model_adapter("mock")
        self.model_name = model_name
        self.results = []
        self.conversation_histories = [[] for _ in range(total)]  # 存储每个请求的对话历史
        self.custom_data = []
        
        # 加载自定义数据
        if self.input_data_type == 'custom' and self.custom_data_path:
            self.load_custom_data()
    
    def load_custom_data(self):
        """加载自定义数据文件"""
        try:
            with open(self.custom_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if 'english_translation' in item:
                            self.custom_data.append(item['english_translation'])
                else:
                    # 处理单个对象的情况
                    if 'english_translation' in data:
                        self.custom_data.append(data['english_translation'])
            print(f"成功加载 {len(self.custom_data)} 条自定义数据")
        except FileNotFoundError:
            print(f"错误: 找不到自定义数据文件 {self.custom_data_path}")
        except json.JSONDecodeError as e:
            print(f"错误: 解析JSON文件时发生错误: {e}")
        except Exception as e:
            print(f"错误: 加载自定义数据时发生错误: {e}")
    
    def generate_test_prompt(self) -> str:
        """生成指定长度的测试prompt，使实际token数接近input_tokens参数
        使用tokenizer词汇表随机选取token，模拟真实模型tokenizer的词汇分布
        """
        import random
        import string
        
        # 随机生成目标token数
        target_tokens = random.randint(self.input_tokens_min, self.input_tokens_max)
        
        # 检查是否使用自定义数据
        if self.input_data_type == 'custom' and self.custom_data:
            # 随机从自定义数据中选择一条
            prompt = random.choice(self.custom_data)
            # 计算当前prompt的估计token数
            # 对于中文，假设每个字符是1个token
            # 对于英文，假设每个单词是1.3个token
            chinese_chars = sum(1 for c in prompt if '\u4e00' <= c <= '\u9fff')
            english_parts = ''.join(c if c.isalnum() or c == ' ' else ' ' for c in prompt)
            english_words = len(english_parts.split())
            current_tokens = chinese_chars + int(english_words * 1.3)
            # 确保current_tokens至少为1
            current_tokens = max(current_tokens, 1)
            
            # 如果数据长度不足，添加填充
            if current_tokens < target_tokens:
                # 计算需要补充的token数
                tokens_to_add = target_tokens - current_tokens
                # 每个字符约0.25个token，所以需要补充的字符数
                fill_chars = int(tokens_to_add / 0.25)
                if fill_chars > 0:
                    filler = ''.join(random.choices(string.ascii_lowercase, k=fill_chars))
                    prompt += " " + filler
            # 如果数据长度超过，进行截断
            elif current_tokens > target_tokens:
                # 计算需要截断的token数
                tokens_to_remove = current_tokens - target_tokens
                # 每个字符约0.25个token，所以需要截断的字符数
                chars_to_remove = int(tokens_to_remove / 0.25)
                if chars_to_remove > 0:
                    prompt = prompt[:-chars_to_remove]
        else:
            # 使用tokenizer词汇表随机选取token
            # 每个token平均约1个token（因为是从tokenizer词汇表中选取的）
            tokens = []
            current_tokens = 0
            
            # 从tokenizer词汇表中随机选取token
            while current_tokens < target_tokens:
                token = random.choice(TOKEN_VOCABULARY)
                # 每个token约1个token，加上空格约0.25个token
                token_count = 1 + 0.25  # 使用平均值估算
                if current_tokens + token_count > target_tokens:
                    break
                tokens.append(token)
                current_tokens += token_count
            
            prompt = " ".join(tokens)
            
            # 如果还不够，添加随机字符填充
            remaining = target_tokens - current_tokens
            if remaining > 0:
                # 每个字符约0.25个token
                fill_chars = int(remaining / 0.25)
                filler = ''.join(random.choices(string.ascii_lowercase, k=fill_chars))
                prompt += " " + filler
        
        # 根据场景添加提示词
        if self.scenario == 'summary':
            summary_prompt = "作为一个智能文本摘要工具，你的任务是把所提供的文本内容的核心要点捕捉并以简洁的方式呈现。摘要将集中于文本的主要论点、关键盖面、重大事件或其他重要信息。请遵循以下指南来优化摘要的结果：1、请先将文本转为中文再提取摘要；2、提供文本的主要内容，但不必要太过详细；3、摘要的目标长度要低于500字；4、摘要的目标长度要高于50字；5、摘要结果必须为中文；6、如果无法提取摘要，则返回空字符串。需要摘要的内容如下："
            prompt = summary_prompt + "\n" + prompt
        elif self.scenario == 'translate':
            translate_prompt = "[system] You are a translator. The user will provide you with text in triple quotes. Translate the text into Chinese. Do not return the translated text int triple quotes.  [USER]"
            prompt = translate_prompt + "\n" + prompt
        elif self.scenario == 'entity_extraction':
            entity_extraction_prompt = """你是一个实体抽取专家，请从以下内容中抽取所有所有提到的人员姓名，及其属性。具体要求如下：1、人名输出形式：(1)如果邮件内容是中文或英文，请以"中文名(英文名)"的形式输出人名。(2)如果邮件内容是其他外文，请以"中文译名（外文名）"的形式输出人名。(3)如果中文名没有对应的英文名，请直接输出中文名，例如:"李毕"。2、请结合上下文判断是否为同一实体。例如，"特朗普" 和 "唐纳德-特朗普"指向同一个人，最终输出时只需保留一个名称。3、利用已知的公共信息或常识来输出人名的官方名称。例如，从邮件中抽取了"特朗普"，输出时应为"唐纳德-特朗普（Donald Trump）"，确保中文名和英文名都是全名。4、针对每个人名，结合上下文，并利用已知的公共信息或常识补充以下属性（若文本中未提及则标注"无"）：（1）所属组织：组织所属国家+完整组织名称，例如："菲律宾国防部"（而非"国防部"）；（2）人物分类：是否是各国政府部分，军队，国际组织的人员的标识；（3）职位：所属组织+完整职位名称，例如："菲律宾国防部长"（而非"部长"）；（4）证件号码：如身份证号、护照号等；（5）联系电话：如手机号、办公电话；（6）国家/地区：输出标准全称，如"中国"、"美国"；（7）详细地址：如"北京朝阳区XX路XX号"；（8）电子邮箱：如zhangsan@company。需要抽取的内容如下："""
            prompt = entity_extraction_prompt + "\n" + prompt
        # print(prompt)
        
        return prompt
    
    def test_single_request(self) -> Dict[str, Any]:
        """测试单个请求的性能"""
        start_time = time.time()
        
        import random
        
        if self.rounds > 0:
            # 多轮问答模式
            messages = []
            total_input_tokens = 0
            total_output_tokens = 0
            total_ttft = 0
            
            for i in range(self.rounds):
                # 生成测试prompt
                prompt = self.generate_test_prompt()
                messages.append({"role": "user", "content": prompt})
                
                # 随机生成输出token数
                output_tokens = random.randint(self.output_tokens_min, self.output_tokens_max)
                
                # 调用模型API
                result = self.model_adapter.generate(messages, output_tokens, ignore_eos=self.ignore_eos, is_multiturn=True, enable_thinking=self.enable_thinking)
                
                # 记录结果
                total_input_tokens += result.get("input_tokens", self.input_tokens)
                total_output_tokens += result.get("output_tokens", output_tokens)
                total_ttft += result.get("ttft", 0)
                
                # 将模型回答添加到对话历史
                messages.append({"role": "assistant", "content": result.get("text", "")})
            
            end_time = time.time()
            total_time = end_time - start_time
            
            return {
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "ttft": total_ttft,
                "total_time": total_time,
                "start_time": start_time,
                "end_time": end_time,
                "rounds": self.rounds,
                "cache_hit": False  # 多轮模式下缓存命中情况复杂，暂不统计
            }
        else:
            # 单轮问答模式
            # 生成测试prompt
            prompt = self.generate_test_prompt()
            
            # 随机生成输出token数
            output_tokens = random.randint(self.output_tokens_min, self.output_tokens_max)
            
            # 调用模型API
            result = self.model_adapter.generate(prompt, output_tokens, ignore_eos=self.ignore_eos, enable_thinking=self.enable_thinking)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            return {
                "input_tokens": result.get("input_tokens", self.input_tokens),
                "output_tokens": result.get("output_tokens", output_tokens),
                "ttft": result.get("ttft", 0),
                "total_time": total_time,
                "start_time": start_time,
                "end_time": end_time,
                "cache_hit": result.get("cache_hit", False)
            }
    
    def run_concurrent_tests(self) -> List[Dict[str, Any]]:
        """运行并发测试，动态提交任务，只有当线程池中有空闲线程时才提交新任务"""
        self.results = []
        completed = 0
        success_count = 0
        failed_count = 0
        total = self.total
        
        print(f"开始执行 {total} 个请求，最大并发数: {self.max_concurrency if self.max_concurrency else total}...")
        
        # 使用max_concurrency限制最大并发数
        max_workers = self.max_concurrency if self.max_concurrency is not None else self.total
        
        # 任务索引
        task_index = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 存储已提交的任务
            future_to_result = {}
            
            # 初始提交任务，直到达到最大并发数或所有任务提交完毕
            while task_index < total and len(future_to_result) < max_workers:
                future = executor.submit(self.test_single_request)
                future_to_result[future] = task_index
                task_index += 1
            
            print(f"[线程池状态] 初始提交: {len(future_to_result)} 个任务正在运行，剩余任务: {total - task_index}")
            
            # 处理完成的任务，并提交新任务
            while future_to_result:
                # 等待至少一个任务完成
                done_futures, _ = concurrent.futures.wait(
                    future_to_result.keys(),
                    return_when=concurrent.futures.FIRST_COMPLETED
                )
                
                # 处理已完成的任务
                for future in done_futures:
                    # 计算当前运行中任务数（减去当前完成的任务）
                    running_count = len(future_to_result) - 1
                    
                    try:
                        result = future.result()
                        self.results.append(result)
                        completed += 1
                        success_count += 1
                        # 显示进度条
                        display_progress_bar(completed, total, prefix='进度', suffix=f'完成 {completed}/{total} 请求 [运行中: {running_count}]', length=30, success=success_count, failed=failed_count)
                    except Exception as exc:
                        print(f'\n测试请求发生异常: {exc}')
                        completed += 1
                        failed_count += 1
                        # 显示进度条
                        display_progress_bar(completed, total, prefix='进度', suffix=f'完成 {completed}/{total} 请求 [运行中: {running_count}]', length=30, success=success_count, failed=failed_count)
                    
                    # 从待处理列表中移除
                    del future_to_result[future]
                    
                    # 如果有更多任务需要提交，提交一个新任务
                    if task_index < total:
                        new_future = executor.submit(self.test_single_request)
                        future_to_result[new_future] = task_index
                        task_index += 1
                        # 打印线程池状态
                        if completed % 5 == 0 or completed == total - 1:  # 每5个任务或最后一个任务时打印
                            print(f"\n[线程池状态] 已完成: {completed}, 运行中: {len(future_to_result)}, 剩余: {total - task_index}")
        
        print(f"\n测试完成，共执行 {completed} 个请求")
        return self.results
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """计算性能指标"""
        if not self.results:
            return {
                "total": self.total,
                "max_concurrency": self.max_concurrency,
                "model_name": self.model_name,
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "avg_ttft": 0,
                "min_ttft": 0,
                "max_ttft": 0,
                "input_throughput": 0,
                "output_throughput": 0,
                "avg_total_time": 0,
                "min_total_time": 0,
                "max_total_time": 0,
                "all_requests_time": 0,
                "total_requests": 0,
                "cache_hit_rate": 0
            }
        
        # 计算总请求数
        total_requests = len(self.results)
        
        # 计算TTFT平均值（转换为毫秒）
        avg_ttft = sum(r['ttft'] for r in self.results) / total_requests * 1000
        
        # 计算TTFT最小和最大值（转换为毫秒）
        min_ttft = min(r['ttft'] for r in self.results) * 1000
        max_ttft = max(r['ttft'] for r in self.results) * 1000
        
        # 计算单个请求延迟总时间
        avg_total_time = sum(r['total_time'] for r in self.results) / total_requests
        
        # 计算最小和最大耗时
        min_total_time = min(r['total_time'] for r in self.results)
        max_total_time = max(r['total_time'] for r in self.results)
        
        # 计算所有请求耗时
        all_requests_time = max(r['end_time'] for r in self.results) - min(r['start_time'] for r in self.results)

        # 计算输入token吞吐率 (tokens/second)
        total_input_tokens = sum(r['input_tokens'] for r in self.results)
        input_throughput = total_input_tokens / all_requests_time
        
        # 计算输出token吞吐率 (tokens/second)
        total_output_tokens = sum(r['output_tokens'] for r in self.results)
        output_throughput = total_output_tokens / all_requests_time
        
        # 计算缓存命中率
        cache_hits = sum(1 for r in self.results if r.get('cache_hit', False))
        cache_hit_rate = cache_hits / total_requests if total_requests > 0 else 0
        
        return {
            "total": total_requests,
            "max_concurrency": self.max_concurrency,
            "model_name": self.model_name,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "avg_ttft": avg_ttft,
            "min_ttft": min_ttft,
            "max_ttft": max_ttft,
            "input_throughput": input_throughput,
            "output_throughput": output_throughput,
            "avg_total_time": avg_total_time,
            "min_total_time": min_total_time,
            "max_total_time": max_total_time,
            "all_requests_time": all_requests_time,
            "total_requests": total_requests,
            "cache_hit_rate": cache_hit_rate,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens
        }
    
    def run(self) -> Dict[str, Any]:
        """运行完整测试并返回结果"""
        if self.rounds > 0 and self.wait_rounds:
            # 按轮次执行测试，等待当前轮次所有请求完成后再开始下一轮
            self.run_round_by_round_tests()
        else:
            # 传统并发测试模式
            self.run_concurrent_tests()
        return self.calculate_metrics()
    
    def run_round_by_round_tests(self) -> List[Dict[str, Any]]:
        """按轮次执行多轮对话测试"""
        self.results = []
        total = self.total
        
        print(f"开始执行 {total} 个请求，共 {self.rounds} 轮...")
        
        # 为每个请求初始化结果存储
        request_results = [{
            "input_tokens": 0,
            "output_tokens": 0,
            "ttft": 0,
            "total_time": 0,
            "start_time": time.time(),
            "end_time": 0,
            "rounds": self.rounds,
            "round_results": [],
            "cache_hit": False
        } for _ in range(total)]
        
        # 计算总请求数
        total_requests = self.rounds * total
        completed_requests = 0
        success_count = 0
        failed_count = 0
        
        import random
        
        # 按轮次执行
        for round_num in range(self.rounds):
            print(f"\n第 {round_num+1} 轮开始...")
            round_start_time = time.time()
            
            # 本轮的结果
            round_results = []
            
            # 使用线程池并发执行本轮的所有请求
            max_workers = self.max_concurrency if self.max_concurrency is not None else total
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 为每个请求提交一个任务
                future_to_request = {}
                # 存储每个请求的output_tokens值，以便后续使用
                request_output_tokens = {}
                for i in range(total):
                    # 生成测试prompt
                    prompt = self.generate_test_prompt()
                    # 添加到对话历史
                    self.conversation_histories[i].append({"role": "user", "content": prompt})
                    # 随机生成输出token数
                    output_tokens = random.randint(self.output_tokens_min, self.output_tokens_max)
                    request_output_tokens[i] = output_tokens
                    # 提交任务
                    future = executor.submit(
                        self.model_adapter.generate,
                        self.conversation_histories[i],
                        output_tokens,
                        self.ignore_eos,
                        True
                    )
                    future_to_request[future] = i
                
                # 收集本轮结果
                completed_in_round = 0
                for future in concurrent.futures.as_completed(future_to_request):
                    request_idx = future_to_request[future]
                    # 获取当前请求的output_tokens值
                    output_tokens = request_output_tokens[request_idx]
                    try:
                        result = future.result()
                        # 记录本轮结果
                        round_result = {
                            "round": round_num + 1,
                            "request_idx": request_idx,
                            "input_tokens": result.get("input_tokens", 0),
                            "output_tokens": result.get("output_tokens", output_tokens),
                            "ttft": result.get("ttft", 0),
                            "time": time.time() - round_start_time
                        }
                        round_results.append(round_result)
                        
                        # 输出本轮指标
                        print(f"  请求 {request_idx+1} - 输入tokens: {round_result['input_tokens']}, 输出tokens: {round_result['output_tokens']}, TTFT: {round_result['ttft']*1000:.2f}ms")
                        
                        # 更新请求的累计结果
                        req_result = request_results[request_idx]
                        req_result["input_tokens"] += round_result["input_tokens"]
                        req_result["output_tokens"] += round_result["output_tokens"]
                        req_result["ttft"] += round_result["ttft"]
                        
                        # 更新完成请求数并显示进度条
                        completed_requests += 1
                        success_count += 1
                        display_progress_bar(completed_requests, total_requests, prefix='进度', suffix=f'完成 {completed_requests}/{total_requests} 请求', length=30, success=success_count, failed=failed_count)
                        req_result["round_results"].append(round_result)
                        
                        # 将模型回答添加到对话历史
                        self.conversation_histories[request_idx].append({"role": "assistant", "content": result.get("text", "")})
                        
                        completed_in_round += 1
                    except Exception as exc:
                        print(f"  请求 {request_idx+1} 发生异常: {exc}")
                        completed_in_round += 1
                        # 即使发生异常，也更新完成请求数并显示进度条
                        completed_requests += 1
                        failed_count += 1
                        display_progress_bar(completed_requests, total_requests, prefix='进度', suffix=f'完成 {completed_requests}/{total_requests} 请求', length=30, success=success_count, failed=failed_count)
            
            round_end_time = time.time()
            round_time = round_end_time - round_start_time
            
            # 计算本轮的指标
            if round_results:
                round_input_tokens = sum(r['input_tokens'] for r in round_results)
                round_output_tokens = sum(r['output_tokens'] for r in round_results)
                round_ttft_values = [r['ttft'] * 1000 for r in round_results]
                round_ttft = sum(round_ttft_values) / len(round_ttft_values)
                min_round_ttft = min(round_ttft_values)
                max_round_ttft = max(round_ttft_values)
                round_input_throughput = round_input_tokens / round_time
                round_output_throughput = round_output_tokens / round_time
                round_total_time_values = [r['time'] for r in round_results]
                round_avg_total_time = sum(round_total_time_values) / len(round_total_time_values)
                round_min_total_time = min(round_total_time_values)
                round_max_total_time = max(round_total_time_values)
                round_cache_hits = sum(1 for r in round_results if r.get('cache_hit', False))
                round_cache_hit_rate = round_cache_hits / len(round_results) if len(round_results) > 0 else 0
                
                print(f"第 {round_num+1} 轮完成，耗时: {round_time:.4f}s")
                print("  本轮指标:")
                print(f"  总请求数: {len(round_results)}")
                print(f"  输入token数: {self.input_tokens}")
                print(f"  输出token数: {self.output_tokens}")
                print(f"  平均TTFT: {round_ttft:.2f}毫秒")
                print(f"  最小TTFT: {min_round_ttft:.2f}毫秒")
                print(f"  最大TTFT: {max_round_ttft:.2f}毫秒")
                print(f"  输入token吞吐率: {round_input_throughput:.2f} tokens/秒")
                print(f"  输出token吞吐率: {round_output_throughput:.2f} tokens/秒")
                print(f"  平均单个请求延迟总时间: {round_avg_total_time:.4f}秒")
                print(f"  最小单个请求延迟总时间: {round_min_total_time:.4f}秒")
                print(f"  最大单个请求延迟总时间: {round_max_total_time:.4f}秒")
                print(f"  所有请求耗时: {round_time:.4f}秒")
                print(f"  缓存命中率: {round_cache_hit_rate*100:.2f}%")
            else:
                print(f"第 {round_num+1} 轮完成，耗时: {round_time:.4f}s")
                print("  本轮无有效结果")
        
        # 所有请求完成，显示完成状态
        display_progress_bar(total_requests, total_requests, prefix='进度', suffix='完成', length=30)
        
        # 完成所有轮次后，设置结束时间
        end_time = time.time()
        
        # 为每个请求计算并输出指标
        print("\n每个请求的指标:")
        print("=" * 80)
        
        # 存储所有轮次的所有请求结果
        all_round_results = []
        
        for i in range(total):
            req_result = request_results[i]
            req_result["end_time"] = end_time
            req_result["total_time"] = end_time - req_result["start_time"]
            
            # 计算该请求的指标
            req_input_tokens = req_result["input_tokens"]
            req_output_tokens = req_result["output_tokens"]
            req_ttft = req_result["ttft"] * 1000 / self.rounds  # 平均TTFT
            req_input_throughput = req_input_tokens / req_result["total_time"]
            req_output_throughput = req_output_tokens / req_result["total_time"]
            
            # 输出该请求的指标
            print(f"请求 {i+1}:")
            print(f"  总输入tokens: {req_input_tokens}, 总输出tokens: {req_output_tokens}")
            print(f"  平均TTFT: {req_ttft:.2f}ms")
            print(f"  输入吞吐率: {req_input_throughput:.2f} tokens/秒, 输出吞吐率: {req_output_throughput:.2f} tokens/秒")
            print(f"  总耗时: {req_result['total_time']:.4f}s")
            print("-" * 80)
            
            # 添加请求级别的结果
            self.results.append(req_result)
            
            # 从round_results中提取每个轮次的结果
            if 'round_results' in req_result:
                for round_result in req_result['round_results']:
                    # 为每个轮次结果添加必要的字段
                    round_result["total_time"] = round_result.get("time", 0)
                    round_result["start_time"] = round_result.get("start_time", req_result["start_time"])
                    round_result["end_time"] = round_result.get("end_time", req_result["end_time"])
                    round_result["cache_hit"] = round_result.get("cache_hit", False)
                    all_round_results.append(round_result)
        
        # 用所有轮次的结果替换self.results，以便calculate_metrics能正确计算
        if all_round_results:
            self.results = all_round_results
        
        print(f"\n测试完成，共执行 {total} 个请求，每个请求 {self.rounds} 轮，总请求数: {len(self.results)}")
        return self.results