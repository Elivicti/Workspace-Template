cmake_minimum_required(VERSION 3.21)

file(GLOB IMAGES CONFIGURE_DEPENDS "images/*.png" "images/*.bmp" "images/*.jpg" "images/*.jpeg")

qt6_add_resources(
	${PROJECT_NAME} "resources"
	PREFIX "/"
	FILES  ${IMAGES}
)