import time
import threading
import concurrent.futures
import json
import os
from typing import List, Dict, Any, Optional
from .model_adapter import ModelAdapter, get_model_adapter

# 加载 tokenizer 词汇表
VOCAB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'vocab.json')

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
    def __init__(self, total: int, input_tokens: int, output_tokens: int, model_adapter: Optional[ModelAdapter] = None, max_concurrency: Optional[int] = None, model_name: Optional[str] = None, ignore_eos: bool = False):
        self.total = total
        self.max_concurrency = max_concurrency
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.ignore_eos = ignore_eos
        self.model_adapter = model_adapter or get_model_adapter("mock")
        self.model_name = model_name
        self.results = []
    
    def generate_test_prompt(self) -> str:
        """生成指定长度的测试prompt，使实际token数接近input_tokens参数
        使用tokenizer词汇表随机选取token，模拟真实模型tokenizer的词汇分布
        """
        import random
        import string
        
        # 目标token数
        target_tokens = self.input_tokens
        
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
        
        return prompt
    
    def test_single_request(self) -> Dict[str, Any]:
        """测试单个请求的性能"""
        start_time = time.time()
        
        # 生成测试prompt
        prompt = self.generate_test_prompt()
        
        # 调用模型API
        result = self.model_adapter.generate(prompt, self.output_tokens, ignore_eos=self.ignore_eos)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        return {
            "input_tokens": result.get("input_tokens", self.input_tokens),
            "output_tokens": result.get("output_tokens", self.output_tokens),
            "ttft": result.get("ttft", 0),
            "total_time": total_time,
            "start_time": start_time,
            "end_time": end_time,
            "cache_hit": result.get("cache_hit", False)
        }
    
    def run_concurrent_tests(self) -> List[Dict[str, Any]]:
        """运行并发测试"""
        self.results = []
        completed = 0
        total = self.total
        
        print(f"开始执行 {total} 个请求...")
        
        # 使用max_concurrency限制最大并发数
        max_workers = self.max_concurrency if self.max_concurrency is not None else self.total
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_result = {executor.submit(self.test_single_request): i for i in range(self.total)}
            for future in concurrent.futures.as_completed(future_to_result):
                try:
                    result = future.result()
                    self.results.append(result)
                    completed += 1
                    # 打印进度条
                    progress = (completed / total) * 100
                    bar_length = 30
                    filled_length = int(bar_length * completed // total)
                    bar = '=' * filled_length + '-' * (bar_length - filled_length)
                    cache_hit = result.get('cache_hit', False)
                    print(f'[{bar}] {completed}/{total} ({progress:.1f}%) - 缓存命中: {"是" if cache_hit else "否"}')
                except Exception as exc:
                    print(f'测试请求发生异常: {exc}')
                    completed += 1
                    # 打印进度条
                    progress = (completed / total) * 100
                    bar_length = 30
                    filled_length = int(bar_length * completed // total)
                    bar = '=' * filled_length + '-' * (bar_length - filled_length)
                    print(f'[{bar}] {completed}/{total} ({progress:.1f}%) - 异常')
        
        print(f"测试完成，共执行 {completed} 个请求")
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
        
        # 计算TTFT平均值（转换为毫秒）
        avg_ttft = sum(r['ttft'] for r in self.results) / len(self.results) * 1000
        
        # 计算TTFT最小和最大值（转换为毫秒）
        min_ttft = min(r['ttft'] for r in self.results) * 1000
        max_ttft = max(r['ttft'] for r in self.results) * 1000
        
    
        # 计算单个请求延迟总时间
        avg_total_time = sum(r['total_time'] for r in self.results) / len(self.results)
        
        # 计算最小和最大耗时
        min_total_time = min(r['total_time'] for r in self.results)
        max_total_time = max(r['total_time'] for r in self.results)
        
        # 计算所有请求耗时
        all_requests_time = max(r['end_time'] for r in self.results) - min(r['start_time'] for r in self.results)

        # 计算输入token吞吐率 (tokens/second)
        input_throughput = sum(r['input_tokens'] for r in self.results) / all_requests_time
        
        # 计算输出token吞吐率 (tokens/second)
        output_throughput = sum(r['output_tokens'] for r in self.results) / all_requests_time
        
        
        # 计算缓存命中率
        cache_hits = sum(1 for r in self.results if r.get('cache_hit', False))
        cache_hit_rate = cache_hits / len(self.results) if len(self.results) > 0 else 0
        
        return {
            "total": self.total,
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
            "total_requests": len(self.results),
            "cache_hit_rate": cache_hit_rate
        }
    
    def run(self) -> Dict[str, Any]:
        """运行完整测试并返回结果"""
        self.run_concurrent_tests()
        return self.calculate_metrics()