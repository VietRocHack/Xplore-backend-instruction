# Xplore-backend-instruction

R&D Notes:

The current way of extracting interesting points in an image is this:
1. Resize the image to XGA (1024 x 768) (this is the relic from when I am working with the computer use from Claude, removable, but I'm too lazy)
2. Apply a grid on top of the images similar to chess, where each square is represented [horizontal alpha][vertical number] like A1, B2, C3...
3. Put the augmented image into Claude model with the appropriate propmt asking for interesting features and grid coordinates (in a form of an array of coordinates, since an interesting point can cover multiple square)
4. The model will spit out some interesting

Problems:
1. The circled parts might not be on the interesting point, sometimes really far away from the given description.

