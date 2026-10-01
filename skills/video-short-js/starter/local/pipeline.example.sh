# A local-first pipeline, read by tools/run.sh. Copy it to local/pipeline.sh and replace the units with the film's own.
#   step <id> <text|vision|path.gguf|-> <command ...>
# A unit is one piece of work the local model can fail and redo on its own: one shot, one sprite, one review.
# Its command runs from the project root with UNIT_ID, UNIT_OUT (write the result there; on success it is renamed
# to local/units/<id>.out) and LOCAL_URL set. It asks the model through `python3 tools/local.py ask`, and exits 75
# when that does (a pause was requested). A finished unit is never run again; delete local/units/<id>.done to redo one.
# Set LOCAL_TEXT_MODEL (and LOCAL_VISION_MODEL, LOCAL_VISION_MMPROJ) first. See references/local-first.md.
#
# step catalogue  -      test -s local/parts.md                                  # the parts kit's catalogue exists (a cloud one-shot or written by hand)
# step cast       text   node tools/gen.mjs cast                                 # world and cast as JSON against the catalogue
# for s in s1 s2 s3 s4; do step "shot-$s" text node tools/gen.mjs shot "$s" || true; done   # a failed shot is left for a takeover
# step look-1     vision python3 tools/judge.py blind shot-s1 shot-s2 shot-s3 shot-s4
# python3 tools/local.py stop                                                     # unload before rendering
# step draft      -      node tools/render.mjs --workers 2 --crf 23
# k=1   # director rounds: stop on running time (paused time does not count) or a round limit, not on a token target alone
# while [ "$(python3 tools/local.py elapsed)" -lt $((4 * 3600)) ] && [ $k -le 6 ]; do
#   step "round-$k" text node tools/gen.mjs round "$k" || break; k=$((k + 1))
# done
echo "local/pipeline.example.sh has no units yet; copy it to local/pipeline.sh and write them"; exit 2
