// Public adapter headers must remain usable from C++ consumers.
#include "sdram_fmc.h"
#if defined(STM32H757xx)
#include "flash_qspi.h"
#else
#include "flash_ospi.h"
#endif
