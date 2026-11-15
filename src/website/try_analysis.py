"""Try the Gemini analysis on real files, from the src/website folder:

    python try_analysis.py <image, folder of images, or PDF> [research file]

Prints the filled-out report. Makes one Gemini call.
"""

import json
import sys

from main import SendPrompt

if len(sys.argv) < 2:
    sys.exit(__doc__)

research = sys.argv[2] if len(sys.argv) > 2 else "research/leopardgecko.json"
print(json.dumps(SendPrompt("test lizard", research, sys.argv[1]), indent=2))
