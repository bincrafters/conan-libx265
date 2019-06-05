#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, tools
import os
import shutil


class LibX265Conan(ConanFile):
    name = "libx265"
    version = "3.0"
    homepage = "http://x265.org"
    url = "https://github.com/bincrafters/conan-libx265"
    description = "x265 is the leading H.265 / HEVC encoder software library"
    license = "https://github.com/someauthor/somelib/blob/master/LICENSES"
    exports_sources = ["CMakeLists.txt", "LICENSE"]
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False], "bit_depth": [8, 10, 12], "HDR10": [True, False]}
    default_options = "shared=False", "fPIC=True", "bit_depth=8", "HDR10=False"
    generators = ['cmake']
    build_requires = "nasm_installer/2.13.02@bincrafters/stable", "ninja_installer/1.8.2@bincrafters/stable"

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def source(self):
        source_url = "https://bitbucket.org/multicoreware/x265/downloads/x265_%s.tar.gz" % self.version
        tools.get(source_url)
        extracted_dir = 'x265_%s' % self.version
        os.rename(extracted_dir, "sources")

    def build(self):
        if self.settings.compiler == 'Visual Studio':
            with tools.vcvars(self.settings, filter_known_paths=False):
                self.build_cmake()
        else:
            self.build_cmake()

    def build_cmake(self):
        if self.settings.os == 'Windows':
            tools.replace_in_file(os.path.join('sources', 'source', 'CMakeLists.txt'),
                                  '${PROJECT_BINARY_DIR}/Debug/x265.pdb',
                                  '${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/x265.pdb')
            tools.replace_in_file(os.path.join('sources', 'source', 'CMakeLists.txt'),
                                  '${PROJECT_BINARY_DIR}/x265.pdb',
                                  '${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/x265.pdb')
        cmake = CMake(self, set_cmake_flags=True)
        cmake.definitions['ENABLE_SHARED'] = self.options.shared
        cmake.definitions['ENABLE_LIBNUMA'] = False
        if self.settings.os == "Macos":
            cmake.definitions['CMAKE_SHARED_LINKER_FLAGS'] = '-Wl,-read_only_relocs,suppress'
        if self.settings.os != 'Windows':
            cmake.definitions['CMAKE_POSITION_INDEPENDENT_CODE'] = self.options.fPIC
            cmake.definitions['ENABLE_PIC'] = self.options.fPIC
        cmake.definitions['HIGH_BIT_DEPTH'] = self.options.bit_depth != 8
        cmake.definitions['MAIN12'] = self.options.bit_depth == 12
        cmake.definitions['ENABLE_HDR10_PLUS'] = self.options.HDR10
        if self.settings.os == "Linux":
            cmake.definitions["PLATFORM_LIBS"] = "dl"
        cmake.configure()
        cmake.build()
        cmake.install()
        if self.settings.os == 'Linux':
            tools.replace_in_file(os.path.join(self.package_folder, 'lib', 'pkgconfig', 'x265.pc'),
                                  'Libs.private:', 'Libs.private: -lpthread')

    def package(self):
        self.copy(pattern="COPYING", src='sources', dst='licenses')
        if self.settings.compiler == 'Visual Studio':
            name = 'libx265.lib' if self.options.shared else 'x265-static.lib'
            shutil.move(os.path.join(self.package_folder, 'lib', name),
                        os.path.join(self.package_folder, 'lib', 'x265.lib'))

    def package_info(self):
        self.cpp_info.libs = ['x265']
        if self.settings.os == "Linux":
            self.cpp_info.libs.extend(['dl', 'pthread'])
