# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION 3.5)

file(MAKE_DIRECTORY
  "/home/embedded/pico/Gh0st/build/_deps/picotool-src"
  "/home/embedded/pico/Gh0st/build/_deps/picotool-build"
  "/home/embedded/pico/Gh0st/build/_deps"
  "/home/embedded/pico/Gh0st/build/picotool/tmp"
  "/home/embedded/pico/Gh0st/build/picotool/src/picotoolBuild-stamp"
  "/home/embedded/pico/Gh0st/build/picotool/src"
  "/home/embedded/pico/Gh0st/build/picotool/src/picotoolBuild-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "/home/embedded/pico/Gh0st/build/picotool/src/picotoolBuild-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "/home/embedded/pico/Gh0st/build/picotool/src/picotoolBuild-stamp${cfgdir}") # cfgdir has leading slash
endif()
