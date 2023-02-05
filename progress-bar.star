
def render_progress_bar():
    width = 6
    end_x = 64
    return animation.Transformation(
        child=render.Box(width=width, height=1, color="#ccc"),
        duration=FPS_ESTIMATE * 60,
        delay=0,
        fill_mode="forwards",
        keyframes=[
            animation.Keyframe(
                percentage=0.0,
                transforms=[
                    animation.Translate(0, 31),
                ],
                # curve="ease_in_out",
            ),
            animation.Keyframe(
                percentage=1.0,
                transforms=[
                    animation.Translate(end_x, 31),
                ],
            ),
        ],
    )
