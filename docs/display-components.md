# LCD / touch components (STM32 HAL)

Each actual controller is a separate package: `stm_lcd_st7789` and
`stm_lcd_st7796` implement SPI panels, `stm_lcd_touch_ft5206` implements
I2C touch, and `stm_lvgl_port` connects board-selected drivers to LVGL 9.
No generic display/touch package is needed. The board project owns pin mux,
HAL handles, power, backlight, delays, bus locking, and the selected module.
The vendor's RGB LTDC timing/profile IDs are module profiles, not identified
controller chips; do not select an SPI driver based on an RGB module ID.

## Integration

1. Confirm the **fitted module** and connector pinout. The board vendor's
   experiment 50 supplies ST7789/ST7796 *SPI module* command sequences;
   experiment 24 supplies FT5206 I2C read registers. An unpopulated display
   connector is not evidence that either display controller is present.
2. In CubeMX, configure the actual module's SPI and CS/DC/RST/BL GPIO; if
   fitted, configure its touch I2C and reset. Board code supplies synchronous
   callbacks. `tx_param` sends command with DC=0, optional data with DC=1;
   `tx_color` sends its `command` (normally `0x2C`) with DC=0 and RGB565 pixels
   with DC=1 in **one protected bus transaction**. Keep CS controlled across
   that transaction; do not allow another user of the bus to interleave.
3. The callback copies or completes using the buffer before return. HAL
   blocking `HAL_SPI_Transmit` is sufficient for initial bring-up. If HAL
   limits transfer size (often 65535 bytes), split the pixel transfer while
   keeping a single RAMWR transaction and a continuous pixel stream. For DMA,
   wait for completion and perform required Cortex-M7 D-cache maintenance.
   The application owns RGB565 wire byte order and module MADCTL/color order.
4. Instantiate *one* panel via `new_panel`, then `reset`, `init`; control
   backlight through board code. Touch is independent: create FT5206 using
   `new_i2c`, optionally reset it, then `read_data`/`get_data`. Its `read_reg`
   callback should read consecutive registers with HAL I2C memory read; the
   7-bit FT5206 address is usually 0x38, while HAL expects `0x38 << 1`.
   Confirm the fitted touch chip and address before connecting it.
5. When using LVGL 9, configure its tick and periodic `lv_timer_handler`.
   Allocate a RGB565 buffer at least one complete line, zero-initialize a
   `stm_lvgl_port_t`, and call `stm_lvgl_port_attach`. Supply board callbacks
   forwarding to the chosen panel's `draw_bitmap` and optional touch reader.
   The panel draw and LVGL callbacks use exclusive end coordinates; LVGL's
   flush area is inclusive, and the port converts it.

A minimal HAL callback for SPI (replace `board_*` with the project's actual
GPIO, SPI handle, bus mutex, and error handling) follows. `board_spi_send`
must send all `size` bytes synchronously in chunks appropriate for HAL:

```c
static int board_tx_param(void *context, uint8_t cmd,
                          const uint8_t *data, size_t size)
{
    board_lcd_io_t *b = context;
    board_lock_spi(b);
    board_cs(b, 0);
    board_dc(b, 0);
    int rc = board_spi_send(b, &cmd, 1);
    if (!rc && size) {
        board_dc(b, 1);
        rc = board_spi_send(b, data, size);
    }
    board_cs(b, 1);
    board_unlock_spi(b);
    return rc;
}

static int board_tx_color(void *context, uint8_t cmd,
                          const void *pixels, size_t bytes)
{
    board_lcd_io_t *b = context;
    board_lock_spi(b);
    board_cs(b, 0);
    board_dc(b, 0);
    int rc = board_spi_send(b, &cmd, 1);
    if (!rc) {
        board_dc(b, 1);
        rc = board_spi_send(b, pixels, bytes);
    }
    board_cs(b, 1);
    board_unlock_spi(b);
    return rc;
}
```

The panel `reset` callback sets its reset line to `high` (1 = released);
`delay_ms` can call `HAL_Delay` after the HAL tick starts. Touch `read_reg`
can call `HAL_I2C_Mem_Read(hi2c, 0x38 << 1, reg, I2C_MEMADD_SIZE_8BIT,
bytes, length, timeout)` after checking that `length` fits HAL's argument
width. The board decides whether the panel is SPI or RGB LTDC. For LTDC,
`stm_lvgl_port` can use a board framebuffer draw callback with correct
stride, color format and D-cache treatment; no unidentified RGB panel
should be published as a chip-specific package.

The drivers are covered by host mock tests, not by physical display testing.
Do not enable the display at default H757 startup until the connected
module's controller, wiring, orientation and backlight have been verified.