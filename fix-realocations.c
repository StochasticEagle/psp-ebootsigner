#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#ifndef __APPLE__
#include <malloc.h>
#else
#include <malloc/malloc.h>
#endif

#include "fix-realocations.h"

int maxelfbuffer = 16 * 1024 * 1024;

int fix_realocations(void) {
  FILE* elf_file = fopen("data_unsigned.psp", "r+b");
	
  if (elf_file) {
    size_t elf_size = 0;

    char* elf_buffer = malloc((size_t)maxelfbuffer);
    if (elf_buffer == NULL) {
      printf("Error: cannot allocate ELF buffer\n");
      fclose(elf_file);
      return -1;
    }

    elf_size = fread(elf_buffer, 1, (size_t)maxelfbuffer, elf_file);
    if (elf_size < sizeof(Elf32_Ehdr_fix)) {
      printf("Error: truncated PRX\n");
      fclose(elf_file);
      free(elf_buffer);
      return -1;
    }

    Elf32_Ehdr_fix* elf_hdr = (Elf32_Ehdr_fix*)&elf_buffer[0];
		
    if (!((elf_hdr->e_ident[0] == 0x7F) && 
	  (strncmp((char*)&elf_hdr->e_ident[1], "ELF", 3) == 0) &&
	  (elf_hdr->e_type == 0xFFA0))) {
      printf("Error: not a PRX\n");

      fclose(elf_file);
      free(elf_buffer);
      return -1;
    }
		
    Elf32_Shdr_fix* sec_hdr = NULL;
    Elf32_Rel* reloc = NULL;

    int i, j;
    for (i = 0; i < elf_hdr->e_shnum; i++) {
      sec_hdr = (Elf32_Shdr_fix*)&elf_buffer[elf_hdr->e_shoff + (i * sizeof(Elf32_Shdr_fix))];
			
      if (sec_hdr->sh_type == 0x700000A0) {
	int num = sec_hdr->sh_size / sizeof(Elf32_Rel);
	for (j = 0; j < num; j++) {
	  reloc = (Elf32_Rel*)&elf_buffer[sec_hdr->sh_offset + (j * sizeof(Elf32_Rel))];
	  if ((reloc->r_info & 0xFF) == 7) {
	    reloc->r_info = (reloc->r_info & 0xFFFFFF00);
	  }
	}
      }
    }
		
    fseek(elf_file, 0, SEEK_SET);
    if (fwrite(elf_buffer, 1, elf_size, elf_file) != elf_size) {
      printf("Error: cannot write PRX\n");
      fclose(elf_file);
      free(elf_buffer);
      return -1;
    }

    fclose(elf_file);
    free(elf_buffer);

  } else {
    printf("Error: cannot open file\n");
    return -1;
  }
  return 0;
}
