#include "include/MDB1.h"
#include <map>
#include <future>
#include <iostream>
#include <deque>
#include <exception>
#include <array>

#include <boost/asio.hpp>
#include <boost/crc.hpp>

#include "../libs/doboz/Compressor.h"
#include "../libs/doboz/Decompressor.h"

namespace dscstools {
	namespace mdb1 {
		constexpr auto MDB1_MAGIC_VALUE = 0x3142444D;
		constexpr auto MDB1_CRYPTED_MAGIC_VALUE = 0x608D920C;

		const uint8_t CRYPT_KEY_1[997] = { 0xD3, 0x53, 0xD2, 0x85, 0xDC, 0x87, 0x77, 0xA7, 0x16, 0xFA, 0x8D, 0x45, 0x9D, 0x14, 0x60, 0x3B, 0x9B, 0x7B, 0xDA, 0xED, 0x25, 0xFD, 0xF5, 0x8D, 0x44, 0xD0, 0xEB, 0x8B, 0xAB, 0x4B, 0x6A, 0x3E, 0x01, 0x28, 0x63, 0xA3, 0xE3, 0x23, 0x63, 0xA3, 0xE2, 0x55, 0x6D, 0xA5, 0x7C, 0xA8, 0xE4, 0xF0, 0x8B, 0xAA, 0x7D, 0x74, 0x40, 0x9C, 0x47, 0x36, 0x9A, 0xAE, 0xB1, 0x19, 0x60, 0x3B, 0x9A, 0xAD, 0xE4, 0xEF, 0xBE, 0x82, 0x76, 0xDA, 0xED, 0x25, 0xFD, 0xF5, 0x8D, 0x45, 0x9C, 0x47, 0x37, 0x67, 0xD6, 0xB9, 0x81, 0xA8, 0xE3, 0x22, 0x96, 0x79, 0x40, 0x9C, 0x48, 0x04, 0x90, 0xAB, 0x4B, 0x6B, 0x0A, 0x5E, 0xA1, 0x48, 0x03, 0xC3, 0x83, 0x42, 0x35, 0xCD, 0x85, 0xDD, 0x55, 0x6C, 0xD7, 0x87, 0x76, 0xD9, 0x20, 0xFC, 0x28, 0x63, 0xA2, 0x15, 0x2D, 0x64, 0x6F, 0x3E, 0x02, 0xF6, 0x5A, 0x6D, 0xA5, 0x7D, 0x74, 0x3F, 0xCE, 0x51, 0x39, 0x00, 0x5C, 0x08, 0xC3, 0x82, 0x75, 0x0C, 0xF8, 0xF3, 0xF2, 0x26, 0xCA, 0x1E, 0x62, 0xD5, 0xED, 0x24, 0x30, 0xCC, 0xB8, 0xB3, 0xB3, 0xB2, 0xE6, 0x89, 0x11, 0xF9, 0xC0, 0x1B, 0xFA, 0x8E, 0x12, 0xC6, 0xE9, 0xF1, 0x58, 0xD4, 0x20, 0xFB, 0x5B, 0x3B, 0x9A, 0xAD, 0xE4, 0xF0, 0x8B, 0xAA, 0x7D, 0x74, 0x40, 0x9C, 0x47, 0x36, 0x9A, 0xAD, 0xE4, 0xF0, 0x8C, 0x77, 0xA7, 0x16, 0xFA, 0x8D, 0x45, 0x9C, 0x47, 0x36, 0x99, 0xE0, 0xBB, 0x1B, 0xFB, 0x5B, 0x3B, 0x9B, 0x7A, 0x0E, 0x91, 0x78, 0x73, 0x73, 0x72, 0xA5, 0x7D, 0x75, 0x0C, 0xF7, 0x26, 0xC9, 0x51, 0x38, 0x34, 0x00, 0x5C, 0x08, 0xC4, 0x50, 0x6C, 0xD7, 0x86, 0xAA, 0x7D, 0x75, 0x0C, 0xF7, 0x26, 0xC9, 0x50, 0x6B, 0x0B, 0x2A, 0xFE, 0xC2, 0xB6, 0x19, 0x60, 0x3C, 0x68, 0xA4, 0xB0, 0x4C, 0x38, 0x33, 0x32, 0x65, 0x3D, 0x34, 0x00, 0x5C, 0x07, 0xF6, 0x59, 0xA0, 0x7C, 0xA7, 0x16, 0xF9, 0xC1, 0xE8, 0x24, 0x2F, 0xFF, 0x8E, 0x12, 0xC6, 0xE9, 0xF0, 0x8C, 0x78, 0x74, 0x40, 0x9B, 0x7A, 0x0E, 0x91, 0x79, 0x41, 0x69, 0x71, 0xD9, 0x20, 0xFB, 0x5B, 0x3B, 0x9A, 0xAE, 0xB2, 0xE6, 0x8A, 0xDE, 0x22, 0x95, 0xAC, 0x18, 0x93, 0x12, 0xC5, 0x1D, 0x95, 0xAC, 0x18, 0x93, 0x13, 0x93, 0x12, 0xC6, 0xEA, 0xBD, 0xB5, 0x4C, 0x38, 0x34, 0x00, 0x5B, 0x3B, 0x9A, 0xAD, 0xE5, 0xBD, 0xB5, 0x4C, 0x38, 0x34, 0xFF, 0x8E, 0x11, 0xF8, 0xF4, 0xC0, 0x1B, 0xFB, 0x5B, 0x3B, 0x9A, 0xAE, 0xB2, 0xE5, 0xBD, 0xB5, 0x4D, 0x05, 0x5D, 0xD5, 0xED, 0x24, 0x30, 0xCC, 0xB8, 0xB4, 0x7F, 0x0F, 0x5E, 0xA2, 0x15, 0x2D, 0x64, 0x6F, 0x3E, 0x02, 0xF6, 0x59, 0xA1, 0x48, 0x03, 0xC2, 0xB6, 0x1A, 0x2E, 0x31, 0x98, 0x13, 0x93, 0x12, 0xC5, 0x1D, 0x95, 0xAD, 0xE4, 0xF0, 0x8C, 0x77, 0xA7, 0x16, 0xF9, 0xC1, 0xE9, 0xF1, 0x58, 0xD4, 0x20, 0xFB, 0x5B, 0x3A, 0xCD, 0x84, 0x10, 0x2C, 0x98, 0x14, 0x5F, 0x6E, 0x72, 0xA5, 0x7C, 0xA8, 0xE4, 0xEF, 0xBE, 0x81, 0xA9, 0xB0, 0x4B, 0x6B, 0x0A, 0x5D, 0xD4, 0x20, 0xFC, 0x27, 0x97, 0x47, 0x37, 0x66, 0x09, 0x90, 0xAB, 0x4A, 0x9E, 0xE2, 0x55, 0x6C, 0xD8, 0x54, 0x9F, 0xAE, 0xB2, 0xE6, 0x89, 0x11, 0xF9, 0xC0, 0x1C, 0xC7, 0xB6, 0x1A, 0x2E, 0x32, 0x66, 0x09, 0x91, 0x79, 0x41, 0x68, 0xA4, 0xB0, 0x4B, 0x6A, 0x3E, 0x02, 0xF6, 0x59, 0xA1, 0x48, 0x04, 0x90, 0xAB, 0x4B, 0x6A, 0x3E, 0x01, 0x28, 0x63, 0xA3, 0xE2, 0x56, 0x39, 0x01, 0x28, 0x63, 0xA2, 0x16, 0xF9, 0xC0, 0x1B, 0xFA, 0x8E, 0x11, 0xF9, 0xC1, 0xE9, 0xF1, 0x59, 0xA1, 0x48, 0x03, 0xC3, 0x82, 0x76, 0xD9, 0x20, 0xFC, 0x27, 0x96, 0x79, 0x40, 0x9B, 0x7B, 0xDA, 0xEE, 0xF1, 0x59, 0xA0, 0x7C, 0xA7, 0x17, 0xC7, 0xB7, 0xE6, 0x89, 0x11, 0xF9, 0xC1, 0xE9, 0xF1, 0x59, 0xA0, 0x7C, 0xA7, 0x16, 0xFA, 0x8D, 0x44, 0xCF, 0x1E, 0x62, 0xD5, 0xED, 0x25, 0xFD, 0xF4, 0xBF, 0x4E, 0xD1, 0xB8, 0xB3, 0xB2, 0xE5, 0xBC, 0xE7, 0x57, 0x06, 0x2A, 0xFE, 0xC2, 0xB5, 0x4D, 0x04, 0x8F, 0xDE, 0x22, 0x96, 0x79, 0x40, 0x9B, 0x7B, 0xDA, 0xED, 0x25, 0xFC, 0x28, 0x64, 0x70, 0x0C, 0xF7, 0x27, 0x97, 0x46, 0x6A, 0x3D, 0x35, 0xCC, 0xB7, 0xE7, 0x56, 0x3A, 0xCD, 0x84, 0x0F, 0x5E, 0xA1, 0x48, 0x04, 0x90, 0xAC, 0x18, 0x94, 0xDF, 0xEE, 0xF1, 0x59, 0xA1, 0x49, 0xD1, 0xB9, 0x80, 0xDC, 0x88, 0x43, 0x03, 0xC3, 0x82, 0x76, 0xD9, 0x20, 0xFB, 0x5B, 0x3A, 0xCE, 0x52, 0x06, 0x29, 0x31, 0x98, 0x14, 0x60, 0x3C, 0x67, 0xD7, 0x86, 0xAA, 0x7E, 0x42, 0x35, 0xCD, 0x85, 0xDD, 0x55, 0x6D, 0xA5, 0x7D, 0x75, 0x0D, 0xC5, 0x1D, 0x94, 0xE0, 0xBB, 0x1A, 0x2D, 0x64, 0x6F, 0x3E, 0x01, 0x29, 0x30, 0xCB, 0xEA, 0xBE, 0x81, 0xA9, 0xB0, 0x4C, 0x38, 0x34, 0xFF, 0x8F, 0xDE, 0x22, 0x95, 0xAD, 0xE5, 0xBD, 0xB5, 0x4C, 0x37, 0x66, 0x09, 0x91, 0x79, 0x40, 0x9C, 0x47, 0x37, 0x67, 0xD7, 0x86, 0xAA, 0x7D, 0x74, 0x40, 0x9C, 0x47, 0x37, 0x66, 0x09, 0x90, 0xAB, 0x4B, 0x6B, 0x0A, 0x5D, 0xD5, 0xEC, 0x58, 0xD3, 0x53, 0xD3, 0x53, 0xD3, 0x52, 0x06, 0x29, 0x30, 0xCC, 0xB8, 0xB4, 0x7F, 0x0F, 0x5F, 0x6F, 0x3E, 0x02, 0xF5, 0x8D, 0x45, 0x9D, 0x14, 0x5F, 0x6F, 0x3E, 0x01, 0x29, 0x31, 0x98, 0x13, 0x93, 0x13, 0x92, 0x45, 0x9D, 0x14, 0x5F, 0x6E, 0x71, 0xD8, 0x54, 0xA0, 0x7B, 0xDB, 0xBA, 0x4D, 0x05, 0x5C, 0x08, 0xC3, 0x82, 0x75, 0x0D, 0xC4, 0x4F, 0x9F, 0xAE, 0xB1, 0x19, 0x60, 0x3C, 0x68, 0xA4, 0xAF, 0x7F, 0x0E, 0x92, 0x45, 0x9D, 0x14, 0x60, 0x3C, 0x67, 0xD7, 0x86, 0xA9, 0xB0, 0x4C, 0x37, 0x67, 0xD6, 0xBA, 0x4D, 0x04, 0x90, 0xAB, 0x4A, 0x9D, 0x14, 0x5F, 0x6E, 0x72, 0xA6, 0x49, 0xD1, 0xB9, 0x80, 0xDB, 0xBB, 0x1B, 0xFA, 0x8D, 0x44, 0xCF, 0x1E, 0x62, 0xD6, 0xB9, 0x80, 0xDC, 0x87, 0x77, 0xA6, 0x49, 0xD1, 0xB9, 0x80, 0xDB, 0xBB, 0x1B, 0xFA, 0x8D, 0x44, 0xD0, 0xEB, 0x8A, 0xDE, 0x21, 0xC8, 0x84, 0x0F, 0x5E, 0xA1, 0x49, 0xD1, 0xB8, 0xB4, 0x80, 0xDC, 0x88, 0x43, 0x03, 0xC3, 0x83, 0x42, 0x35, 0xCD, 0x84, 0x0F, 0x5E, 0xA1, 0x48, 0x04, 0x8F, 0xDF, 0xEE, 0xF1, 0x59, 0xA0, 0x7C, 0xA7, 0x17, 0xC7, 0xB6, 0x19, 0x61, 0x08, 0xC4, 0x4F, 0x9F, 0xAE, 0xB1, 0x18, 0x93, 0x12, 0xC6, 0xEA, 0xBD, 0xB4, 0x80, 0xDC, 0x88, 0x44, 0xD0, 0xEB, 0x8B, 0xAB, 0x4B, 0x6B, 0x0B, 0x2A, 0xFE, 0xC2, 0xB6, 0x1A, 0x2D, 0x65, 0x3D, 0x35, 0xCC, 0xB8, 0xB4, 0x80, 0xDC, 0x88, 0x43, 0x03, 0xC2, 0xB5, 0x4D, 0x04, 0x8F, 0xDF, 0xEF, 0xBE, 0x81, 0xA8, 0xE3, 0x23, 0x63, 0xA2, 0x16, 0xF9, 0xC0, 0x1B, 0xFA, 0x8E, 0x11, 0xF9, 0xC1, 0xE9, 0xF0, 0x8B, 0xAA, 0x7E, 0x42, 0x35, 0xCD, 0x84, 0x10, 0x2C, 0x97, 0x46, 0x69, 0x70, 0x0C, 0xF7, 0x27, 0x97, 0x47, 0x37, 0x66, 0x0A, 0x5E, 0xA1, 0x49, 0xD0, 0xEC, 0x58, 0xD4, 0x20, 0xFC, 0x28, 0x64, 0x6F, 0x3E, 0x01, 0x28, 0x63, 0xA2, 0x15, 0x2C, 0x98, 0x14, 0x60, 0x3B, 0x9B };
		const uint8_t CRYPT_KEY_2[991] = { 0x92, 0x85, 0x1D, 0xD4, 0x60, 0x7B, 0x1B, 0x3B, 0xDB, 0xFA, 0xCE, 0x92, 0x85, 0x1D, 0xD5, 0x2D, 0xA4, 0xF0, 0xCB, 0x2A, 0x3D, 0x74, 0x80, 0x1B, 0x3B, 0xDB, 0xFA, 0xCD, 0xC5, 0x5C, 0x47, 0x77, 0xE7, 0x97, 0x87, 0xB6, 0x5A, 0xAD, 0x24, 0x6F, 0x7E, 0x82, 0xB6, 0x5A, 0xAD, 0x25, 0x3D, 0x75, 0x4C, 0x78, 0xB4, 0xC0, 0x5B, 0x7B, 0x1A, 0x6D, 0xE4, 0x2F, 0x3E, 0x42, 0x76, 0x1A, 0x6D, 0xE4, 0x30, 0x0C, 0x37, 0xA7, 0x57, 0x47, 0x76, 0x1A, 0x6E, 0xB1, 0x59, 0xE1, 0xC9, 0x91, 0xB9, 0xC1, 0x28, 0xA3, 0x22, 0xD5, 0x2C, 0xD7, 0xC7, 0xF6, 0x99, 0x21, 0x08, 0x03, 0x02, 0x35, 0x0C, 0x38, 0x73, 0xB3, 0xF2, 0x66, 0x49, 0x10, 0x6C, 0x17, 0x06, 0x6A, 0x7E, 0x82, 0xB5, 0x8C, 0xB8, 0xF4, 0x00, 0x9C, 0x87, 0xB6, 0x59, 0xE1, 0xC9, 0x90, 0xEC, 0x97, 0x87, 0xB7, 0x26, 0x0A, 0x9E, 0x21, 0x09, 0xD1, 0xF9, 0x01, 0x68, 0xE4, 0x2F, 0x3F, 0x0F, 0x9F, 0xEF, 0xFF, 0xCE, 0x92, 0x86, 0xE9, 0x31, 0xD8, 0x94, 0x20, 0x3B, 0xDB, 0xFA, 0xCE, 0x92, 0x85, 0x1C, 0x08, 0x03, 0x02, 0x36, 0xD9, 0x60, 0x7C, 0xE8, 0x63, 0xE3, 0x62, 0x15, 0x6D, 0xE5, 0xFD, 0x34, 0x3F, 0x0F, 0x9F, 0xEF, 0xFE, 0x02, 0x36, 0xDA, 0x2D, 0xA4, 0xEF, 0xFE, 0x01, 0x69, 0xB1, 0x59, 0xE0, 0xFB, 0x9B, 0xBA, 0x8D, 0x85, 0x1D, 0xD4, 0x60, 0x7B, 0x1B, 0x3B, 0xDB, 0xFB, 0x9A, 0xEE, 0x32, 0xA5, 0xBC, 0x28, 0xA3, 0x23, 0xA3, 0x23, 0xA3, 0x23, 0xA3, 0x22, 0xD6, 0xFA, 0xCE, 0x92, 0x86, 0xE9, 0x30, 0x0C, 0x38, 0x74, 0x7F, 0x4F, 0xDF, 0x2F, 0x3E, 0x41, 0xA8, 0x23, 0xA3, 0x23, 0xA3, 0x22, 0xD5, 0x2D, 0xA4, 0xF0, 0xCC, 0xF7, 0x67, 0x16, 0x39, 0x40, 0xDB, 0xFB, 0x9B, 0xBA, 0x8D, 0x84, 0x4F, 0xDE, 0x62, 0x16, 0x39, 0x40, 0xDC, 0xC7, 0xF6, 0x99, 0x21, 0x08, 0x04, 0xD0, 0x2C, 0xD8, 0x94, 0x1F, 0x6F, 0x7E, 0x82, 0xB5, 0x8D, 0x85, 0x1C, 0x08, 0x04, 0xD0, 0x2C, 0xD8, 0x93, 0x53, 0x12, 0x05, 0x9C, 0x88, 0x84, 0x4F, 0xDE, 0x61, 0x48, 0x44, 0x0F, 0x9E, 0x22, 0xD5, 0x2D, 0xA5, 0xBC, 0x28, 0xA4, 0xF0, 0xCB, 0x2B, 0x0A, 0x9D, 0x55, 0xAC, 0x58, 0x14, 0xA0, 0xBC, 0x28, 0xA3, 0x22, 0xD6, 0xF9, 0x00, 0x9B, 0xBA, 0x8E, 0x52, 0x45, 0xDC, 0xC7, 0xF7, 0x67, 0x17, 0x06, 0x69, 0xB1, 0x58, 0x13, 0xD2, 0xC6, 0x29, 0x71, 0x18, 0xD4, 0x5F, 0xAE, 0xF1, 0x98, 0x54, 0xE0, 0xFC, 0x68, 0xE4, 0x2F, 0x3F, 0x0E, 0xD1, 0xF9, 0x01, 0x69, 0xB1, 0x58, 0x14, 0x9F, 0xEE, 0x32, 0xA5, 0xBD, 0xF4, 0xFF, 0xCE, 0x91, 0xB9, 0xC0, 0x5B, 0x7B, 0x1B, 0x3A, 0x0D, 0x05, 0x9C, 0x87, 0xB6, 0x5A, 0xAE, 0xF2, 0x65, 0x7C, 0xE8, 0x63, 0xE3, 0x62, 0x15, 0x6C, 0x17, 0x07, 0x36, 0xD9, 0x61, 0x48, 0x43, 0x43, 0x42, 0x75, 0x4C, 0x78, 0xB3, 0xF3, 0x33, 0x72, 0xE6, 0xCA, 0x5E, 0xE1, 0xC8, 0xC3, 0xC3, 0xC3, 0xC2, 0xF6, 0x99, 0x21, 0x08, 0x04, 0xD0, 0x2C, 0xD8, 0x94, 0x1F, 0x6E, 0xB2, 0x26, 0x0A, 0x9E, 0x22, 0xD5, 0x2D, 0xA4, 0xEF, 0xFF, 0xCF, 0x5F, 0xAF, 0xBE, 0xC2, 0xF5, 0xCC, 0xF7, 0x66, 0x4A, 0xDE, 0x61, 0x49, 0x11, 0x39, 0x41, 0xA8, 0x24, 0x70, 0x4C, 0x77, 0xE7, 0x97, 0x86, 0xEA, 0xFD, 0x34, 0x40, 0xDB, 0xFA, 0xCE, 0x92, 0x86, 0xE9, 0x31, 0xD8, 0x93, 0x52, 0x46, 0xAA, 0xBD, 0xF5, 0xCD, 0xC5, 0x5D, 0x14, 0xA0, 0xBB, 0x5A, 0xAE, 0xF2, 0x65, 0x7C, 0xE7, 0x97, 0x86, 0xEA, 0xFD, 0x34, 0x3F, 0x0E, 0xD2, 0xC5, 0x5D, 0x15, 0x6D, 0xE5, 0xFD, 0x35, 0x0C, 0x37, 0xA7, 0x57, 0x47, 0x77, 0xE7, 0x97, 0x87, 0xB6, 0x59, 0xE1, 0xC8, 0xC4, 0x8F, 0x1E, 0xA2, 0x55, 0xAD, 0x24, 0x70, 0x4C, 0x77, 0xE7, 0x96, 0xB9, 0xC0, 0x5C, 0x47, 0x76, 0x1A, 0x6D, 0xE4, 0x2F, 0x3E, 0x41, 0xA9, 0xF1, 0x98, 0x53, 0x12, 0x06, 0x69, 0xB0, 0x8C, 0xB7, 0x26, 0x0A, 0x9D, 0x54, 0xDF, 0x2E, 0x72, 0xE5, 0xFD, 0x34, 0x3F, 0x0F, 0x9F, 0xEE, 0x32, 0xA5, 0xBD, 0xF4, 0xFF, 0xCF, 0x5E, 0xE1, 0xC9, 0x91, 0xB9, 0xC0, 0x5C, 0x48, 0x43, 0x42, 0x75, 0x4C, 0x78, 0xB3, 0xF2, 0x65, 0x7C, 0xE7, 0x96, 0xB9, 0xC1, 0x28, 0xA3, 0x22, 0xD5, 0x2D, 0xA5, 0xBC, 0x27, 0xD6, 0xF9, 0x01, 0x69, 0xB1, 0x58, 0x13, 0xD2, 0xC6, 0x2A, 0x3D, 0x75, 0x4D, 0x45, 0xDC, 0xC7, 0xF6, 0x99, 0x21, 0x09, 0xD0, 0x2C, 0xD7, 0xC7, 0xF7, 0x67, 0x16, 0x39, 0x41, 0xA8, 0x24, 0x6F, 0x7E, 0x82, 0xB6, 0x59, 0xE1, 0xC9, 0x90, 0xEC, 0x98, 0x53, 0x12, 0x05, 0x9C, 0x87, 0xB6, 0x5A, 0xAD, 0x25, 0x3C, 0xA8, 0x24, 0x70, 0x4C, 0x77, 0xE6, 0xCA, 0x5E, 0xE2, 0x95, 0xED, 0x64, 0xB0, 0x8B, 0xEB, 0xCB, 0x2B, 0x0A, 0x9D, 0x55, 0xAC, 0x58, 0x13, 0xD3, 0x92, 0x86, 0xEA, 0xFD, 0x34, 0x3F, 0x0E, 0xD1, 0xF8, 0x34, 0x40, 0xDC, 0xC8, 0xC4, 0x8F, 0x1E, 0xA1, 0x89, 0x50, 0xAB, 0x8A, 0x1D, 0xD5, 0x2D, 0xA4, 0xF0, 0xCB, 0x2B, 0x0A, 0x9D, 0x55, 0xAC, 0x57, 0x46, 0xA9, 0xF0, 0xCC, 0xF7, 0x67, 0x17, 0x07, 0x36, 0xDA, 0x2E, 0x71, 0x19, 0xA1, 0x88, 0x83, 0x83, 0x83, 0x82, 0xB6, 0x5A, 0xAD, 0x25, 0x3D, 0x74, 0x80, 0x1C, 0x08, 0x04, 0xCF, 0x5F, 0xAF, 0xBF, 0x8E, 0x51, 0x78, 0xB3, 0xF3, 0x32, 0xA5, 0xBD, 0xF5, 0xCD, 0xC4, 0x90, 0xEC, 0x97, 0x87, 0xB7, 0x27, 0xD7, 0xC6, 0x29, 0x70, 0x4B, 0xAB, 0x8B, 0xEB, 0xCB, 0x2A, 0x3D, 0x74, 0x7F, 0x4F, 0xDE, 0x62, 0x15, 0x6D, 0xE5, 0xFD, 0x34, 0x40, 0xDB, 0xFA, 0xCD, 0xC4, 0x90, 0xEB, 0xCA, 0x5E, 0xE1, 0xC9, 0x91, 0xB9, 0xC1, 0x28, 0xA4, 0xEF, 0xFF, 0xCE, 0x92, 0x85, 0x1D, 0xD4, 0x5F, 0xAE, 0xF2, 0x65, 0x7D, 0xB5, 0x8D, 0x84, 0x50, 0xAC, 0x57, 0x47, 0x76, 0x1A, 0x6E, 0xB1, 0x59, 0xE0, 0xFB, 0x9B, 0xBB, 0x5B, 0x7A, 0x4D, 0x45, 0xDD, 0x95, 0xED, 0x65, 0x7D, 0xB4, 0xBF, 0x8F, 0x1F, 0x6F, 0x7E, 0x81, 0xE9, 0x30, 0x0C, 0x37, 0xA6, 0x89, 0x50, 0xAC, 0x57, 0x46, 0xAA, 0xBD, 0xF5, 0xCC, 0xF7, 0x66, 0x4A, 0xDE, 0x61, 0x48, 0x44, 0x10, 0x6C, 0x18, 0xD4, 0x5F, 0xAF, 0xBE, 0xC1, 0x28, 0xA3, 0x23, 0xA2, 0x55, 0xAC, 0x58, 0x14, 0xA0, 0xBC, 0x28, 0xA4, 0xEF, 0xFF, 0xCF, 0x5E, 0xE1, 0xC8, 0xC4, 0x8F, 0x1E, 0xA1, 0x88, 0x83, 0x82, 0xB5, 0x8C, 0xB7, 0x27, 0xD6, 0xF9, 0x00, 0x9C, 0x87, 0xB6, 0x59, 0xE1, 0xC9, 0x90, 0xEC, 0x98, 0x53, 0x13, 0xD3, 0x93, 0x53, 0x12, 0x06, 0x6A, 0x7D, 0xB5, 0x8C, 0xB8, 0xF4, 0xFF, 0xCF, 0x5F, 0xAF, 0xBE, 0xC2, 0xF5, 0xCD, 0xC4, 0x8F, 0x1F, 0x6E, 0xB1, 0x59, 0xE1, 0xC8, 0xC4, 0x90, 0xEB, 0xCA, 0x5E, 0xE2, 0x95, 0xED, 0x64, 0xAF, 0xBE, 0xC1, 0x28, 0xA3, 0x23, 0xA3, 0x23, 0xA3, 0x23, 0xA2, 0x55, 0xAD, 0x25, 0x3D, 0x74, 0x7F, 0x4F, 0xDE, 0x62, 0x16, 0x39, 0x40, 0xDC, 0xC7, 0xF7, 0x67, 0x17, 0x06, 0x69, 0xB1, 0x58, 0x13, 0xD3, 0x93, 0x53, 0x13, 0xD2, 0xC5, 0x5C, 0x47, 0x77 };

		template<std::size_t SIZE>
		void cryptArray(std::array<char, SIZE>& array, uint64_t offset) {
			cryptArray(array.data(), array.size(), offset);
		}

		void cryptArray(char* array, std::size_t size, uint64_t offset) {
			for (int i = 0; i < size; i++)
				array[i] ^= CRYPT_KEY_1[(offset + i) % 997] ^ CRYPT_KEY_2[(offset + i) % 991];
		}

		// helper structures
		struct MDB1Header {
			uint32_t magicValue;
			uint16_t fileEntryCount;
			uint16_t fileNameCount;
			uint32_t dataEntryCount;
			uint32_t dataStart;
			uint32_t totalSize;
		};

		struct TreeNode {
			int16_t compareBit;
			uint16_t left = 0;
			uint16_t right = 0;
			std::string name;
		};

		struct CompressionResult {
			uint32_t originalSize = 0;
			uint32_t size = 0;
			uint32_t crc = 0;
			std::unique_ptr<char[]> data;
		};

		class mdb1_ifstream : public boost::filesystem::ifstream {
		private:
			bool doCrypt = false;
		public:
			mdb1_ifstream(const boost::filesystem::path path, bool doCrypt) : doCrypt(doCrypt), boost::filesystem::ifstream(path, std::ios::in | std::ios::binary) {}
			mdb1_ifstream(const boost::filesystem::path path) : boost::filesystem::ifstream(path, std::ios::in | std::ios::binary) {
				uint32_t val = 0;
				read(reinterpret_cast<char*>(&val), 4);
				doCrypt = val == MDB1_CRYPTED_MAGIC_VALUE;
				seekg(0);
			}

			std::istream& read(char* dst, std::streamsize count) {
				std::streampos offset = tellg();
				boost::filesystem::ifstream::read(dst, count);
				if (doCrypt)
					cryptArray(dst, count, offset);
				return *this;
			}
		};

		class mdb1_ofstream : public boost::filesystem::ofstream {
			using boost::filesystem::ofstream::ofstream;
		private:
			bool doCrypt = false;
		public:
			mdb1_ofstream(const boost::filesystem::path path, bool doCrypt = false) : doCrypt(doCrypt), boost::filesystem::ofstream(path, std::ios::out | std::ios::binary) {}

			std::ostream& write(char* dst, std::streamsize count) {
				if (doCrypt)
					cryptArray(dst, count, tellp());
				boost::filesystem::ofstream::write(dst, count);
				return *this;
			}
		};

		ArchiveInfo getArchiveInfo(const boost::filesystem::path source) {
			if (!boost::filesystem::is_regular_file(source))
				throw std::invalid_argument("Error: Source path doesn't point to a file, aborting.");

			ArchiveInfo info;

			mdb1_ifstream input(source);

			MDB1Header header;
			input.read(reinterpret_cast<char*>(&header), 0x14);

			if (header.magicValue == MDB1_CRYPTED_MAGIC_VALUE)
				info.status = encrypted;
			else if (header.magicValue == MDB1_MAGIC_VALUE)
				info.status = decrypted;
			else {
				info.status = invalid;
				return info;
			}

			auto fileEntries = std::make_unique<FileEntry[]>(header.fileEntryCount);
			auto nameEntries = std::make_unique<FileNameEntry[]>(header.fileNameCount);
			auto dataEntries = std::make_unique<DataEntry[]>(header.dataEntryCount);

			input.read(reinterpret_cast<char*>(fileEntries.get()), header.fileEntryCount * sizeof(FileEntry));
			input.read(reinterpret_cast<char*>(nameEntries.get()), header.fileNameCount * sizeof(FileNameEntry));
			input.read(reinterpret_cast<char*>(dataEntries.get()), header.dataEntryCount * sizeof(DataEntry));

			info.magicValue = header.magicValue;
			info.fileCount = header.fileEntryCount;
			info.dataStart = header.dataStart;

			for (int i = 0; i < header.fileEntryCount; i++) {
				FileInfo fileInfo;
				fileInfo.file = fileEntries[i];
				fileInfo.name = nameEntries[i];
				if (fileInfo.file.compareBit != 0xFFFF && fileInfo.file.dataId != 0xFFFF)
					fileInfo.data = dataEntries[fileEntries[i].dataId];

				info.fileInfo.push_back(fileInfo);
			}

			return info;
		}

		std::string buildMDB1Path(std::string fileName, std::string extension) {
			if (extension.length() == 3)
				extension = extension.append(" ");

			std::replace(fileName.begin(), fileName.end(), '/', '\\');

			char name[0x41];
			strncpy(name, extension.c_str(), 4);
			strncpy(name + 4, fileName.c_str(), 0x3C);
			name[0x40] = 0; // prevent overflow

			return std::string(name);
		}

		FileInfo findFileEntry(const std::vector<FileInfo>& entries, std::string path) {
			std::replace(path.begin(), path.end(), '/', '\\');
			size_t delimPos = path.rfind('.');

			if (delimPos == -1 || path.size() - delimPos > 5)
				return entries[0];

			std::string finalName = buildMDB1Path(path.substr(0, delimPos), path.substr(delimPos + 1));

			FileInfo currentNode = entries[1];

			while (true) {
				bool isSet = ((finalName[currentNode.file.compareBit >> 3]) >> (currentNode.file.compareBit & 7)) & 1;
				FileInfo nextNode = entries[isSet ? currentNode.file.right : currentNode.file.left];

				if (nextNode.file.compareBit <= currentNode.file.compareBit)
					return std::string(reinterpret_cast<char*>(&nextNode.name)) == finalName ? nextNode : entries[0];

				currentNode = nextNode;
			}

			return entries[0];
		}

		void dobozCompress(const boost::filesystem::path source, const boost::filesystem::path target) {
			if (boost::filesystem::equivalent(source, target))
				throw std::invalid_argument("Error: input and output path must be different!");
			if (!boost::filesystem::is_regular_file(source))
				throw std::invalid_argument("Error: input path is not a file.");

			if (!boost::filesystem::exists(target)) {
				if (target.has_parent_path())
					boost::filesystem::create_directories(target.parent_path());
			}
			else if (!boost::filesystem::is_regular_file(target))
				throw std::invalid_argument("Error: target path already exists and is not a file.");

			boost::filesystem::ifstream input(source, std::ios::in | std::ios::binary);
			boost::filesystem::ofstream output(target, std::ios::out | std::ios::binary);

			input.seekg(0, std::ios::end);
			std::streampos length = input.tellg();
			input.seekg(0, std::ios::beg);

			auto data = std::make_unique<char[]>(length);
			input.read(data.get(), length);

			doboz::Compressor comp;
			size_t destSize;

			auto outputData = std::make_unique<char[]>(comp.getMaxCompressedSize(length));
			doboz::Result result = comp.compress(data.get(), length, outputData.get(), comp.getMaxCompressedSize(length), destSize);

			if (result != doboz::RESULT_OK)
				throw std::runtime_error("Error: something went wrong while compressing, doboz error code: " + std::to_string(result));

			output.write(outputData.get(), destSize);
		}

		void dobozDecompress(const boost::filesystem::path source, const boost::filesystem::path target) {
			if (boost::filesystem::equivalent(source, target))
				throw std::invalid_argument("Error: input and output path must be different!");
			if (!boost::filesystem::is_regular_file(source))
				throw std::invalid_argument("Error: input path is not a file.");

			if (!boost::filesystem::exists(target)) {
				if (target.has_parent_path())
					boost::filesystem::create_directories(target.parent_path());
			}
			else if (!boost::filesystem::is_regular_file(target))
				throw std::invalid_argument("Error: target path already exists and is not a file.");

			boost::filesystem::ifstream input(source, std::ios::in | std::ios::binary);
			boost::filesystem::ofstream output(target, std::ios::out | std::ios::binary);
			input.seekg(0, std::ios::end);
			std::streampos length = input.tellg();
			input.seekg(0, std::ios::beg);

			auto data = std::make_unique<char[]>(length);
			input.read(data.get(), length);

			doboz::CompressionInfo info;
			doboz::Decompressor decomp;

			decomp.getCompressionInfo(data.get(), length, info);

			if (info.compressedSize != length || info.version != 0)
				throw std::runtime_error("Error: input file is not doboz compressed!");

			auto outputData = std::make_unique<char[]>(info.uncompressedSize);

			auto result = decomp.decompress(data.get(), length, outputData.get(), info.uncompressedSize);

			if(result != doboz::RESULT_OK)
				throw std::runtime_error("Error: something went wrong while decompressing, doboz error code: " + std::to_string(result));

			std::cout << info.compressedSize << " " << info.uncompressedSize << " " << info.version << std::endl;

			output.write(outputData.get(), info.uncompressedSize);
		}

		void extractMDB1File(const boost::filesystem::path source, const boost::filesystem::path targetDir, FileInfo fileInfo, uint64_t offset, bool decompress) {
			mdb1_ifstream input(source);
			doboz::Decompressor decomp;

			if (fileInfo.file.compareBit == 0xFFFF || fileInfo.file.dataId == 0xFFFF)
				return;

			DataEntry data = fileInfo.data;

			boost::filesystem::path path(targetDir / fileInfo.name.toPath());
			if (path.has_parent_path())
				boost::filesystem::create_directories(path.parent_path());
			mdb1_ofstream output(path, false);

			auto outputSize = decompress ? data.size : data.compSize;
			auto outputArr = std::make_unique<char[]>(outputSize);
			input.seekg(data.offset + offset);

			if (data.compSize == data.size || !decompress)
				input.read(outputArr.get(), outputSize);
			else {
				auto dataArr = std::make_unique<char[]>(data.compSize);
				input.read(dataArr.get(), data.compSize);
				doboz::Result result = decomp.decompress(dataArr.get(), data.compSize, outputArr.get(), data.size);

				if (result != doboz::RESULT_OK)
					throw std::runtime_error("Error while decompressing '" + fileInfo.name.toString() + "'. doboz error code : " + std::to_string(result));
			}

			output.write(outputArr.get(), outputSize);

			if (!output.good())
				throw std::runtime_error("Error: something went wrong while writing " + path.string());
		}

		void extractMDB1File(const boost::filesystem::path source, const boost::filesystem::path target, FileInfo fileInfo, const bool decompress) {
			extractMDB1File(source, target, fileInfo, getArchiveInfo(source).dataStart, decompress);
		}

		void extractMDB1File(const boost::filesystem::path source, const boost::filesystem::path target, std::string fileName, const bool decompress) {
			ArchiveInfo info = getArchiveInfo(source);
			FileInfo fileInfo = findFileEntry(info.fileInfo, fileName);

			if (fileInfo.file.compareBit == 0xFFFF || fileInfo.file.dataId == 0xFFFF)
				throw std::invalid_argument("MDB1 File Extraction: File not found in archive");

			extractMDB1File(source, target, fileInfo, info.dataStart, decompress);
		}

		void extractMDB1(const boost::filesystem::path source, const boost::filesystem::path target, bool decompress) {
			if (boost::filesystem::exists(target) && !boost::filesystem::is_directory(target))
				throw std::invalid_argument("Error: Target path exists and is not a directory, aborting.");
			if (!boost::filesystem::is_regular_file(source))
				throw std::invalid_argument("Error: Source path doesn't point to a file, aborting.");

			ArchiveInfo info = getArchiveInfo(source);
			if (info.status == invalid)
				throw std::invalid_argument("Error: not a MDB1 file. Value: " + std::to_string(info.magicValue));

			for (FileInfo& fileInfo : info.fileInfo)
				extractMDB1File(source, target, fileInfo, info.dataStart, decompress);
		}

		TreeNode findFirstBitMismatch(const int16_t first, const std::vector<std::string>& nodeless, const std::vector<std::string>& withNode) {
			if (withNode.size() == 0)
				return { first, 0, 0, nodeless[0] };

			for (int16_t i = first; i < 512; i++) {
				bool set = false;
				bool unset = false;

				for (auto file : withNode) {
					if ((file[i >> 3] >> (i & 7)) & 1)
						set = true;
					else
						unset = true;

					if (set && unset)
						return { i, 0, 0, nodeless[0] };
				}

				auto itr = std::find_if(nodeless.begin(), nodeless.end(), [set, unset, i](const std::string &file) {
					bool val = (file[i >> 3] >> (i & 7)) & 1;
					return val && unset || !val && set;
					});

				if (itr != nodeless.end())
					return { i, 0, 0, *itr };
			}

			return { -1, 0xFFFF, 0, "" };
		}

		std::vector<TreeNode> generateTree(const boost::filesystem::path path) {
			std::vector<std::string> fileNames;

			boost::filesystem::recursive_directory_iterator itr(path);

			for (auto i : itr) {
				if (boost::filesystem::is_regular_file(i)) {
					std::string ext = i.path().extension().string().substr(1, 5);
					std::string filePath = boost::filesystem::relative(i.path(), path).replace_extension("").string();

					fileNames.push_back(buildMDB1Path(filePath, ext));
				}
			}

			// sort filesnames for consistent results
			std::sort(fileNames.begin(), fileNames.end(), [](std::string first, std::string second) {
				int result = first.compare(4, first.size() - 4, second, 4, second.size() - 4);
				return (result == 0 ? first.compare(0, 4, second, 0, 4) : result) < 0;
				});

			struct QueueEntry {
				uint16_t parentNode;
				int16_t val1;
				std::vector<std::string> list;
				std::vector<std::string> nodeList;
				bool left;
			};

			std::vector<TreeNode> nodes = { { (int16_t)0xFFFF, 0, 0, "" } };
			std::deque<QueueEntry> queue = { { 0, -1, fileNames, std::vector<std::string>(), false } };

			while (!queue.empty()) {
				QueueEntry entry = queue.front();
				queue.pop_front();
				TreeNode &parent = nodes[entry.parentNode];

				std::vector <std::string> nodeless;
				std::vector <std::string> withNode;

				for (auto file : entry.list) {
					if (std::find(entry.nodeList.begin(), entry.nodeList.end(), file) == entry.nodeList.end())
						nodeless.push_back(file);
					else
						withNode.push_back(file);
				}

				if (nodeless.size() == 0) {
					auto firstFile = entry.list[0];
					auto itr = std::find_if(nodes.begin(), nodes.end(), [firstFile](const TreeNode &node) { return node.name == firstFile; });
					ptrdiff_t offset = std::distance(nodes.begin(), itr);

					if (entry.left)
						parent.left = (uint16_t)offset;
					else
						parent.right = (uint16_t)offset;

					continue;
				}

				TreeNode child = findFirstBitMismatch(entry.val1 + 1, nodeless, withNode);

				if (entry.left)
					parent.left = (uint16_t)nodes.size();
				else
					parent.right = (uint16_t)nodes.size();

				std::vector<std::string> left;
				std::vector<std::string> right;

				for (auto file : entry.list) {
					if ((file[child.compareBit >> 3] >> (child.compareBit & 7)) & 1)
						right.push_back(file);
					else
						left.push_back(file);
				}

				std::vector<std::string> newNodeList = entry.nodeList;
				newNodeList.push_back(child.name);

				if (left.size() > 0) queue.push_front({ static_cast<uint16_t>(nodes.size()), child.compareBit, left, newNodeList, true });
				if (right.size() > 0) queue.push_front({ static_cast<uint16_t>(nodes.size()), child.compareBit, right, newNodeList, false });
				nodes.push_back(child);
			}

			return nodes;
		}

		CompressionResult getFileData(const boost::filesystem::path path, const CompressMode compress) {
			boost::filesystem::ifstream input(path, std::ios::in | std::ios::binary);

			input.seekg(0, std::ios::end);
			std::streampos length = input.tellg();
			input.seekg(0, std::ios::beg);

			auto data = std::make_unique<char[]>(length);
			input.read(data.get(), length);

			boost::crc_32_type crc;
			if (compress == advanced)
				crc.process_bytes(data.get(), length);

			if (!input.good())
				throw std::runtime_error("Error: something went wrong while reading " + path.string());
			
			doboz::Decompressor decomp;
			doboz::CompressionInfo info;
			doboz::Result result = decomp.getCompressionInfo(data.get(), length, info);

			if (length != 0) {
				if (result == doboz::RESULT_OK && info.uncompressedSize != 0 && info.version == 0 && info.compressedSize == length)
					return { (uint32_t)info.uncompressedSize, (uint32_t)info.compressedSize, crc.checksum(), std::move(data) };

				if (compress >= normal) {
					doboz::Compressor comp;
					size_t destSize;
					auto outputData = std::make_unique<char[]>(comp.getMaxCompressedSize(length));
					doboz::Result res = comp.compress(data.get(), length, outputData.get(), comp.getMaxCompressedSize(length), destSize);

					if (res != doboz::RESULT_OK)
						throw std::runtime_error("Error: something went wrong while compressing, doboz error code: " + std::to_string(res));

					if (destSize + 4 < static_cast<size_t>(length))
						return { (uint32_t)length, (uint32_t)destSize, crc.checksum(), std::move(outputData) };
				}
			}

			return { (uint32_t)length, (uint32_t)length, crc.checksum(), std::move(data) };
		}

		void packMDB1(const boost::filesystem::path source, const boost::filesystem::path target, const CompressMode compress, bool doCrypt, std::ostream& progressStream) {
			if (!boost::filesystem::is_directory(source))
				throw std::invalid_argument("Error: source path is not a directory.");

			if (!boost::filesystem::exists(target)) {
				if (target.has_parent_path())
					boost::filesystem::create_directories(target.parent_path());
			}
			else if (!boost::filesystem::is_regular_file(target))
				throw std::invalid_argument("Error: target path already exists and is not a file.");

			progressStream << "Generating file tree..." << std::endl;
			std::vector<boost::filesystem::path> files;
			std::vector<TreeNode> nodes = generateTree(source);

			for (auto i : boost::filesystem::recursive_directory_iterator(source))
				if (boost::filesystem::is_regular_file(i))
					files.push_back(i);

			std::sort(files.begin(), files.end());

			// start compressing files
			std::map<std::string, std::promise<CompressionResult>> futureMap;

			size_t coreCount = std::thread::hardware_concurrency();
			boost::asio::thread_pool pool(coreCount * 2); // twice the core count to account for blocking threads
			progressStream << "Start compressing files with " << coreCount * 2 << " threads..." << std::endl;

			for (auto file : files) {
				futureMap[file.string()] = std::promise<CompressionResult>();

				boost::asio::post(pool, [&promise = futureMap[file.string()], file, compress]{
					try {
						promise.set_value(getFileData(file, compress));
					}
					catch (std::exception ex) {
						promise.set_exception(std::make_exception_ptr(ex));
					} });
			}

			std::vector<FileEntry> header1(files.size() + 1);
			std::vector<FileNameEntry> header2(files.size() + 1);
			std::vector<DataEntry> header3;

			mdb1_ofstream output(target, doCrypt);

			size_t dataStart = 0x14 + (1 + files.size()) * 0x08 + (1 + files.size()) * 0x40 + (files.size()) * 0x0C;
			MDB1Header header = { MDB1_MAGIC_VALUE, (uint16_t)(files.size() + 1), (uint16_t)(files.size() + 1), (uint32_t)files.size(), (uint32_t)dataStart };

			header1[0] = { (int16_t)0xFFFF, 0xFFFF, 0, 1 };
			header2[0] = FileNameEntry();

			uint32_t fileCount = 0;
			size_t numFiles = files.size();
			progressStream << "Start writing " << numFiles << " files..." << std::endl;

			uint32_t offset = 0;
			std::map<uint32_t, size_t> dataMap;

			for (auto file : files) {
				if (++fileCount % 200 == 0)
					progressStream << "File " << fileCount << " of " << numFiles << std::endl;

				// fill in name
				FileNameEntry entry2;

				std::string ext = file.extension().string().substr(1, 5);
				if (ext.length() == 3)
					ext = ext.append(" ");

				// strncpy weirdness intended
				std::string filePath = boost::filesystem::relative(file, source).replace_extension("").string();
				std::replace(filePath.begin(), filePath.end(), '/', '\\');

				strncpy(entry2.extension, ext.c_str(), 4);
				strncpy(entry2.name, filePath.c_str(), 0x3C);

				// find corresponding node, create table entry
				auto found = std::find_if(nodes.begin(), nodes.end(), [entry2](const TreeNode &node) { return node.name == entry2.extension; });
				if (found == nodes.end())
					throw std::runtime_error("Fatal error: Couldn't find node for " + entry2.toString());

				TreeNode treeNode = *found;
				ptrdiff_t nodeId = std::distance(nodes.begin(), found);

				// get data and write it
				CompressionResult data = futureMap[file.string()].get_future().get();
				futureMap.erase(file.string());

				bool hasEntry = compress == advanced && dataMap.find(data.crc) != dataMap.end();

				// store table entries
				header1[nodeId] = { treeNode.compareBit, (uint16_t)(hasEntry ? dataMap.at(data.crc) : header3.size()), treeNode.left, treeNode.right };
				header2[nodeId] = entry2;
				if (!hasEntry) {
					dataMap[data.crc] = header3.size();
					header3.push_back({ offset, data.originalSize, data.size });

					output.seekp(dataStart + offset);
					output.write(data.data.get(), data.size);
					offset += data.size;
				}
			}

			progressStream << "Writing and compressing files complete." << std::endl;

			// write file table and header
			output.seekp(0x14);

			for (auto entry : header1)
				output.write(reinterpret_cast<char*>(&entry), 0x08);
			for (auto entry : header2)
				output.write(reinterpret_cast<char*>(&entry), 0x40);
			for (auto entry : header3)
				output.write(reinterpret_cast<char*>(&entry), 0x0C);

			output.seekp(0x00);
			output.seekp(0, std::ios::end);
			std::streamoff length = output.tellp();
			output.seekp(0, std::ios::beg);

			header.totalSize = (uint32_t)length;
			header.dataEntryCount = (uint32_t)header3.size();
			output.write(reinterpret_cast<char*>(&header), 0x14);

			if (!output.good())
				throw std::runtime_error("Error: something went wrong with the output stream.");
		}

		void cryptFile(const boost::filesystem::path source, const boost::filesystem::path target) {
			if (boost::filesystem::equivalent(source, target))
				throw std::invalid_argument("Error: input and output path must be different!");
			if (!boost::filesystem::is_regular_file(source))
				throw std::invalid_argument("Error: input path is not a file.");

			if (!boost::filesystem::exists(target)) {
				if (target.has_parent_path())
					boost::filesystem::create_directories(target.parent_path());
			}
			else if (!boost::filesystem::is_regular_file(target))
				throw std::invalid_argument("Error: target path already exists and is not a file.");

			mdb1_ifstream input(source, false);
			mdb1_ofstream output(target, true);

			std::streamsize offset = 0;

			std::array<char, 0x2000> inArr;

			while (!input.eof()) {
				input.read(inArr.data(), 0x2000);
				std::streamsize count = input.gcount();
				output.write(inArr.data(), count);
				offset += count;
			}
		}
	}
}